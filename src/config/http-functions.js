// http-functions.js - ENHANCED VERSION WITH RENDER TYPE SUPPORT
import { ok, badRequest, notFound } from 'wix-http-functions';
import { verifyPaymentSignature } from 'backend/razorPay.jsw';
import wixData from 'wix-data';
import { syncSearchIndex } from 'backend/search';
import { fetchNewArrivals, fetchMensProducts, fetchWomensProducts, fetchTopChoices } from 'backend/repeaterAPIendpoints/repeaterUtils.jsw';
import { orderService } from 'backend/orderService.jsw';

/**
 * Extracts the user ID from the request headers or URL query parameters.
 * @param {Object} request - The HTTP request object.
 * @return {string|null} The extracted user ID, or null if not found.
 */
function extractUserId(request) {
    if (request.headers['x-user-id']) {
        return request.headers['x-user-id'];
    }
    const url = new URL(request.url);
    return url.searchParams.get('userId') || url.searchParams.get('user_id');
}

/**
 * Determines whether an incoming HTTP request is likely from a bot.
 * 
 * Checks for the presence of a specific header or common bot indicators in the user-agent string.
 * @param {Object} request - The HTTP request object containing headers.
 * @return {boolean} True if the request appears to be from a bot; otherwise, false.
 */
function isBotRequest(request) {
    const userAgent = request.headers['user-agent'] || '';
    return request.headers['x-bot-request'] === 'true' || 
           userAgent.toLowerCase().includes('bot') ||
           userAgent.toLowerCase().includes('ai-customer-service');
}

/**
 * Parses an input parameter into an array of cleaned order ID strings.
 * 
 * Accepts a comma-separated string or an array, trims whitespace from each ID, and removes empty entries.
 * @param {string|string[]} orderIdsParam - Comma-separated order IDs or an array of order ID strings.
 * @return {string[]} An array of non-empty, trimmed order ID strings.
 */
function parseOrderIds(orderIdsParam) {
    if (!orderIdsParam) return [];
    if (typeof orderIdsParam === 'string') {
        return orderIdsParam.split(',').map(id => id.trim()).filter(id => id.length > 0);
    }
    if (Array.isArray(orderIdsParam)) {
        return orderIdsParam.filter(id => id && id.trim().length > 0);
    }
    return [];
}

/**
 * Handles Razorpay webhook POST requests, verifying event authenticity and preventing duplicate processing.
 *
 * Parses the incoming webhook payload, checks for duplicate event IDs, verifies the payment signature, and stores valid events in the "WebhookEvents" collection. Returns a JSON response indicating whether the webhook was processed, already handled, or deferred due to errors.
 */
export async function post_razorpayWebhook(request) {
    const options = { headers: { 'Content-Type': 'application/json' } };
    try {
        const rawBody = await request.body.text();
        const parsedBody = JSON.parse(rawBody);
        const signature = request.headers['x-razorpay-signature'];
        const eventId = request.headers['x-razorpay-event-id'];
        console.log("Webhook received at:", new Date().toISOString());
        console.log("Webhook payload:", parsedBody);
        console.log("Event ID:", eventId);

        const existingEvent = await wixData.get("WebhookEvents", eventId, { suppressAuth: true })
            .catch(() => null);
        if (existingEvent) {
            console.log(`Duplicate event ${eventId} already processed`);
            options.body = { message: "Webhook already processed" };
            return ok(options);
        }

        const isValid = await verifyPaymentSignature({ signature }, rawBody);
        console.log("Signature Verification:", isValid);

        if (!isValid) {
            console.error("Invalid signature");
            options.body = { message: "Invalid signature, event accepted but not processed" };
            return ok(options);
        }

        await wixData.insert("WebhookEvents", {
            _id: eventId,
            event: parsedBody.event,
            orderId: parsedBody.payload?.payment?.entity?.order_id || parsedBody.payload?.order?.entity?.id,
            paymentId: parsedBody.payload?.payment?.entity?.id,
            status: parsedBody.payload?.order?.entity?.status || parsedBody.payload?.payment?.entity?.status,
            payload: parsedBody,
            receivedAt: new Date()
        }, { suppressAuth: true });

        console.log(`Webhook ${parsedBody.event} processed for order ${parsedBody.payload?.payment?.entity?.order_id || 'unknown'}`);

        options.body = { message: "Webhook processed" };
        return ok(options);
    } catch (error) {
        console.error("Webhook error:", error);
        options.body = { message: "Webhook accepted, processing deferred" };
        return ok(options);
    }
}

/**
 * Triggers synchronization of the search index and returns the result.
 * @returns {Promise<object>} An object containing the result of the search index synchronization, or an error message if the operation fails.
 */
export async function post_syncSearchIndex(request) {
    try {
        const result = await syncSearchIndex();
        return ok({ body: result });
    } catch (error) {
        console.error("Error in syncSearchIndex:", error);
        return ok({ body: { success: false, error: error.message } });
    }
}

/**
 * Handles HTTP requests to retrieve a list of new arrival products.
 *
 * Accepts an optional `limit` query parameter to specify the maximum number of products to return (default is 15).
 * Responds with a JSON object containing the product list, success status, and contextual metadata.
 * Returns a 400 Bad Request with error details if an error occurs during retrieval.
 */
export async function get_getNewArrivals(request) {
    try {
        const url = new URL(request.url);
        const limitParam = url.searchParams.get("limit");
        const limit = parseInt(limitParam) || 15;

        const products = await fetchNewArrivals(limit);

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: products,
                context: { limit: limit, type: "new_arrivals" }
            }
        });
    } catch (error) {
        console.error("Error in getNewArrivals:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: error.message,
                code: "SERVER_ERROR",
                context: { type: "new_arrivals" }
            }
        });
    }
}

/**
 * Handles HTTP requests to retrieve men's products with an optional limit.
 * 
 * Parses the `limit` query parameter (defaulting to 15 if not provided), fetches the specified number of men's products, and returns them in a JSON response. On error, returns a 400 Bad Request with error details.
 */
export async function get_getMensProducts(request) {
    try {
        const url = new URL(request.url);
        const limitParam = url.searchParams.get("limit");
        const limit = parseInt(limitParam) || 15;
        const products = await fetchMensProducts(limit);

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: products,
                context: { limit: limit, type: "mens_products" }
            }
        });
    } catch (error) {
        console.error("Error in getMensProducts:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: error.message,
                code: "SERVER_ERROR",
                context: { type: "mens_products" }
            }
        });
    }
}

/**
 * Handles HTTP requests to retrieve a list of women's products with an optional limit.
 * 
 * Parses the `limit` query parameter (defaulting to 15 if not provided), fetches the specified number of women's products, and returns them in a structured JSON response. On error, returns a 400 Bad Request with error details.
 */
export async function get_getWomensProducts(request) {
    try {
        const url = new URL(request.url);
        const limitParam = url.searchParams.get("limit");
        const limit = parseInt(limitParam) || 15;
        const products = await fetchWomensProducts(limit);

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: products,
                context: { limit: limit, type: "womens_products" }
            }
        });
    } catch (error) {
        console.error("Error in getWomensProducts:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: error.message,
                code: "SERVER_ERROR",
                context: { type: "womens_products" }
            }
        });
    }
}

/**
 * Handles product search requests with optional category filtering and result limiting.
 *
 * Extracts the search query, category, and limit from the request's query parameters. Searches the "allProducts" collection for products whose names contain the query string, optionally filtering by category. Returns a JSON response with a list of matching product summaries or an error if the query parameter is missing or a server error occurs.
 *
 * @param {Request} request - The HTTP request containing search parameters.
 * @returns {Promise<Response>} A JSON response with the search results or an error message.
 */
export async function get_searchProducts(request) {
    try {
        const url = new URL(request.url);
        const query = url.searchParams.get("q") || url.searchParams.get("query");
        const category = url.searchParams.get("category");
        const limit = parseInt(url.searchParams.get("limit")) || 20;

        if (!query) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "Search query is required",
                    code: "MISSING_PARAMETER",
                    context: { type: "search_products" }
                }
            });
        }

        let searchQuery = wixData.query("allProducts")
            .contains("name", query)
            .limit(limit);

        if (category) {
            searchQuery = searchQuery.include("collections");
        }

        const results = await searchQuery.find();

        let filteredProducts = results.items;

        if (category) {
            filteredProducts = results.items.filter(item => {
                return item.collections?.some(collection =>
                    collection.name.toLowerCase() === category.toLowerCase()
                );
            });
        }

        const products = filteredProducts.map(item => ({
            _id: item._id,
            productId: item._id,
            name: item.name,
            slug: item.slug3 || item.slug,
            price: item.price,
            formattedPrice: item.formattedPrice,
            discountedPrice: item.discountedPrice,
            formattedDiscountedPrice: item.formattedDiscountedPrice || item.formattedPrice,
            inStock: item.inStock,
            mediaItems: item.mediaItems || [],
            productOptions: item.productOptions || {},
            description: item.description || ""
        }));

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: products,
                context: { query: query, limit: limit, category: category, type: "search_products" }
            }
        });
    } catch (error) {
        console.error("Error in searchProducts:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: error.message,
                code: "SERVER_ERROR",
                context: { type: "search_products" }
            }
        });
    }
}

/**
 * Handles an HTTP request to retrieve detailed information for a single product by its ID.
 *
 * Validates the presence of the product ID in the query parameters, fetches the product from the "allProducts" collection, and returns a structured JSON response with product details. Responds with appropriate error messages if the product ID is missing or the product is not found.
 */
export async function get_getProduct(request) {
    try {
        const url = new URL(request.url);
        const productId = url.searchParams.get("id");

        if (!productId) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "Product ID is required",
                    code: "MISSING_PARAMETER",
                    context: { type: "get_product" }
                }
            });
        }

        const result = await wixData.get("allProducts", productId);

        if (!result) {
            return ok({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "Product not found",
                    code: "NOT_FOUND",
                    context: { type: "get_product", productId: productId }
                }
            });
        }

        const product = {
            _id: result._id,
            productId: result._id,
            name: result.name,
            slug: result.slug3 || result.slug,
            price: result.price,
            formattedPrice: result.formattedPrice,
            discountedPrice: result.discountedPrice,
            formattedDiscountedPrice: result.formattedDiscountedPrice || result.formattedPrice,
            inStock: result.inStock,
            mediaItems: result.mediaItems || [],
            productOptions: result.productOptions || {},
            description: result.description || ""
        };

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: [product],
                context: { type: "get_product", productId: productId }
            }
        });
    } catch (error) {
        console.error("Error in getProduct:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: error.message,
                code: "SERVER_ERROR",
                context: { type: "get_product" }
            }
        });
    }
}

/**
 * Handles HTTP requests to retrieve items for a specific order.
 *
 * Validates the presence of the order ID in the request, extracts the user ID, and fetches order items using the order service. Returns a JSON response with the order items, contextual metadata (such as total items, status groups, and unique statuses), or an error message if the request is invalid or the service call fails.
 */
export async function get_getOrderItems(request) {
    try {
        const url = new URL(request.url);
        const orderId = url.searchParams.get("orderId");
        const userId = extractUserId(request);

        if (!orderId) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "Order ID is required",
                    code: "MISSING_PARAMETER",
                    context: { type: "order_items", orderId: orderId }
                }
            });
        }

        console.log(`getOrderItems: orderId=${orderId}, userId=${userId}, isBot=${isBotRequest(request)}`);

        const result = await orderService.getOrderItems(orderId, userId);

        if (!result.success) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: result.error,
                    code: result.code,
                    context: { type: "order_items", orderId: orderId }
                }
            });
        }

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: result.metric_value,
                context: {
                    type: "order_items",
                    orderId: orderId,
                    totalItems: result.context.totalItems,
                    statusGroups: result.context.statusGroups,
                    uniqueStatuses: result.context.uniqueStatuses,
                    hasMultipleItems: result.context.totalItems > 1
                }
            }
        });
    } catch (error) {
        console.error("Error in getOrderItems:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: "Failed to retrieve order items",
                code: "SERVER_ERROR",
                context: { type: "order_items" }
            }
        });
    }
}

/**
 * Handles HTTP requests to retrieve a summary of a specific order for a user.
 *
 * Validates the presence of the `orderId` query parameter and extracts the user ID from the request. Calls the order service to obtain the order summary, including item count, status details, and mixed status flag. Returns a structured JSON response with success status, summary data, and contextual metadata. Responds with a 400 Bad Request if required parameters are missing or if the service call fails.
 */
export async function get_getOrderSummary(request) {
    try {
        const url = new URL(request.url);
        const orderId = url.searchParams.get("orderId");
        const userId = extractUserId(request);

        if (!orderId) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "Order ID is required",
                    code: "MISSING_PARAMETER",
                    context: { type: "order_summary", orderId: orderId }
                }
            });
        }

        console.log(`getOrderSummary: orderId=${orderId}, userId=${userId}, isBot=${isBotRequest(request)}`);

        const result = await orderService.getOrderSummary(orderId, userId);

        if (!result.success) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: result.error,
                    code: result.code,
                    context: { type: "order_summary", orderId: orderId }
                }
            });
        }

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: result.metric_value,
                context: {
                    type: "order_summary",
                    orderId: orderId,
                    itemCount: result.context.itemCount,
                    statusDetails: result.context.statusDetails,
                    hasMixedStatus: result.context.hasMixedStatus
                }
            }
        });
    } catch (error) {
        console.error("Error in getOrderSummary:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: "Failed to retrieve order summary",
                code: "SERVER_ERROR",
                context: { type: "order_summary" }
            }
        });
    }
}

/**
 * Handles an HTTP request to retrieve a paginated list of orders for a user, with optional inclusion of order items.
 *
 * Extracts the user ID from the request and supports pagination via `limit` and `offset` query parameters. The `includeItems` parameter controls whether order items are included in the response. Returns a structured JSON response with order data, pagination context, and error details if applicable.
 */
export async function get_getUserOrders(request) {
    try {
        const url = new URL(request.url);
        const userId = extractUserId(request);
        const limitParam = url.searchParams.get("limit");
        const offsetParam = url.searchParams.get("offset");
        const includeItemsParam = url.searchParams.get("includeItems");

        const limit = parseInt(limitParam) || 6;
        const offset = parseInt(offsetParam) || 0;
        const includeItems = includeItemsParam === 'true';

        if (!userId) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "User ID is required",
                    code: "MISSING_USER_ID",
                    context: { type: "user_orders" }
                }
            });
        }

        console.log(`getUserOrders: userId=${userId}, limit=${limit}, offset=${offset}, includeItems=${includeItems}`);

        const result = await orderService.getUserOrders(userId, {
            limit,
            offset,
            includeItems
        });

        if (!result.success) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: result.error,
                    code: result.code,
                    context: { type: "user_orders", userId: userId }
                }
            });
        }

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: result.metric_value,
                context: {
                    type: "user_orders",
                    totalOrders: result.context.totalOrders,
                    totalAvailable: result.context.totalAvailable,
                    hasMore: result.context.hasMore,
                    pagination: result.context.pagination
                }
            }
        });
    } catch (error) {
        console.error("Error in getUserOrders:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: "Failed to retrieve user orders",
                code: "SERVER_ERROR",
                context: { type: "user_orders" }
            }
        });
    }
}

/**
 * Retrieves the statuses of multiple orders for a user based on provided order IDs.
 *
 * Validates the presence and correctness of the `orderIds` query parameter, extracts the user ID, and calls the order service to fetch status information for each order. Returns a structured JSON response with status details, including lists of requested, successful, and failed orders, as well as a summary. Responds with an error if parameters are missing, invalid, or if the service call fails.
 */
export async function get_getMultipleOrderStatus(request) {
    try {
        const url = new URL(request.url);
        const userId = extractUserId(request);
        const orderIdsParam = url.searchParams.get("orderIds");

        if (!orderIdsParam) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "Order IDs parameter is required (comma-separated)",
                    code: "MISSING_PARAMETER",
                    context: { type: "multiple_order_status", example: "?orderIds=order1,order2,order3" }
                }
            });
        }

        const orderIds = parseOrderIds(orderIdsParam);

        if (orderIds.length === 0) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "At least one valid order ID is required",
                    code: "INVALID_PARAMETER",
                    context: { type: "multiple_order_status" }
                }
            });
        }

        console.log(`getMultipleOrderStatus: orderIds=${orderIds.join(',')}, userId=${userId}`);

        const result = await orderService.getMultipleOrderStatus(orderIds, userId);

        if (!result.success) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: result.error,
                    code: result.code,
                    context: { type: "multiple_order_status", orderIds: orderIds }
                }
            });
        }

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: result.metric_value,
                context: {
                    type: "multiple_order_status",
                    requestedOrders: result.context.requestedOrders,
                    successfulOrders: result.context.successfulOrders,
                    failedOrders: result.context.failedOrders,
                    failed: result.context.failed,
                    summary: result.context.summary
                }
            }
        });
    } catch (error) {
        console.error("Error in getMultipleOrderStatus:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: "Failed to retrieve multiple order status",
                code: "SERVER_ERROR",
                context: { type: "multiple_order_status" }
            }
        });
    }
}

/**
 * Retrieves the most recent orders for a user, with optional inclusion of render type information.
 *
 * Extracts the user ID from the request and returns up to a specified number of the user's latest orders (default 1, maximum 20). The response can include render type details if requested (enabled by default). Returns a structured JSON response with order data and contextual metadata. Responds with an error if the user ID is missing, the count is out of range, or if an internal error occurs.
 */
export async function get_getLastOrders(request) {
    try {
        const url = new URL(request.url);
        const userId = extractUserId(request);
        const countParam = url.searchParams.get("count");
        const includeRenderTypesParam = url.searchParams.get("includeRenderTypes");
        
        const count = parseInt(countParam) || 1;
        const includeRenderTypes = includeRenderTypesParam !== 'false'; // Default to true

        console.log(`[getLastOrders] Input: userId=${userId}, count=${count}, includeRenderTypes=${includeRenderTypes}`);

        if (!userId) {
            console.error("[getLastOrders] Error: User ID is required");
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "User ID is required",
                    code: "MISSING_USER_ID",
                    context: { type: "last_orders" }
                }
            });
        }

        if (count < 1 || count > 20) {
            console.error(`[getLastOrders] Error: Invalid count=${count}, must be between 1 and 20`);
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "Count must be between 1 and 20",
                    code: "INVALID_PARAMETER",
                    context: { type: "last_orders" }
                }
            });
        }

        // Call enhanced orderService with render types support
        const result = await orderService.getLastOrders(userId, count, includeRenderTypes);
        console.log(`[getLastOrders] OrderService Result: success=${result.success}, orders_count=${result.metric_value.length}, renderTypes=${result.context.includeRenderTypes}`);

        if (!result.success) {
            console.error(`[getLastOrders] OrderService Error: ${result.error}, code=${result.code}`);
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: result.error,
                    code: result.code,
                    context: { type: "last_orders", userId: userId }
                }
            });
        }

        console.log(`[getLastOrders] Returning ${result.metric_value.length} orders with render types for userId=${userId}`);
        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: result.metric_value,
                context: {
                    type: "last_orders",
                    requestedCount: count,
                    actualCount: result.metric_value.length,
                    context: result.context.context,
                    includeRenderTypes: result.context.includeRenderTypes,
                    renderTypesEnabled: result.context.renderTypesEnabled
                }
            }
        });
    } catch (error) {
        console.error("[getLastOrders] Exception:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: "Failed to retrieve last orders: " + error.message,
                code: "SERVER_ERROR",
                context: { type: "last_orders" }
            }
        });
    }
}

/**
 * Handles HTTP requests to retrieve a user's recent orders within a specified number of days.
 *
 * Validates the presence of a user ID and ensures the days parameter is within the allowed range (1–365). Returns a JSON response containing the user's recent orders, total order count, and date range context. Responds with an error if parameters are missing or invalid, or if the order retrieval fails.
 */
export async function get_getRecentOrders(request) {
    try {
        const url = new URL(request.url);
        const userId = extractUserId(request);
        const daysParam = url.searchParams.get("days");

        const days = parseInt(daysParam) || 30;

        if (!userId) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "User ID is required",
                    code: "MISSING_USER_ID",
                    context: { type: "recent_orders" }
                }
            });
        }

        if (days < 1 || days > 365) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "Days must be between 1 and 365",
                    code: "INVALID_PARAMETER",
                    context: { type: "recent_orders" }
                }
            });
        }

        console.log(`getRecentOrders: userId=${userId}, days=${days}`);

        const result = await orderService.getRecentOrders(userId, days);

        if (!result.success) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: result.error,
                    code: result.code,
                    context: { type: "recent_orders", userId: userId }
                }
            });
        }

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: result.metric_value,
                context: {
                    type: "recent_orders",
                    totalOrders: result.context.totalOrders,
                    dateRange: result.context.dateRange,
                    context: result.context.context
                }
            }
        });
    } catch (error) {
        console.error("Error in getRecentOrders:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: "Failed to retrieve recent orders",
                code: "SERVER_ERROR",
                context: { type: "recent_orders" }
            }
        });
    }
}

/**
 * Retrieves orders for a user filtered by a specific status.
 *
 * Extracts the user ID and status from the request query parameters, validates their presence, and fetches orders matching the status for the user. Supports an optional limit on the number of results (default 10). Returns a structured JSON response with the filtered orders and contextual metadata, or an error response if validation fails or the service encounters an error.
 */
export async function get_getOrdersByStatus(request) {
    try {
        const url = new URL(request.url);
        const userId = extractUserId(request);
        const status = url.searchParams.get("status");
        const limitParam = url.searchParams.get("limit");

        const limit = parseInt(limitParam) || 10;

        if (!userId) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "User ID is required",
                    code: "MISSING_USER_ID",
                    context: { type: "orders_by_status" }
                }
            });
        }

        if (!status) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "Status parameter is required",
                    code: "MISSING_PARAMETER",
                    context: { type: "orders_by_status", examples: ["Pending", "Processing", "Shipped", "Delivered", "Cancelled", "Partially Processed", "Partially Shipped", "Partially Cancelled"] }
                }
            });
        }

        console.log(`getOrdersByStatus: userId=${userId}, status=${status}, limit=${limit}`);

        const result = await orderService.getOrdersByStatus(userId, status, limit);

        if (!result.success) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: result.error,
                    code: result.code,
                    context: { type: "orders_by_status", status: status }
                }
            });
        }

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: result.metric_value,
                context: {
                    type: "orders_by_status",
                    totalOrders: result.context.totalOrders,
                    filterStatus: result.context.filterStatus
                }
            }
        });
    } catch (error) {
        console.error("Error in getOrdersByStatus:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: "Failed to retrieve orders by status",
                code: "SERVER_ERROR",
                context: { type: "orders_by_status" }
            }
        });
    }
}

/**
 * Handles an HTTP request to retrieve aggregated order statistics for a user.
 * 
 * Validates the presence of a user ID in the request, calls the order service to obtain order statistics, and returns a structured JSON response with the results or error details.
 * 
 * @returns {Promise<Response>} A JSON response containing user order statistics and context, or an error message if the request is invalid or the service fails.
 */
export async function get_getUserOrderStats(request) {
    try {
        const url = new URL(request.url);
        const userId = extractUserId(request);

        if (!userId) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "User ID is required",
                    code: "MISSING_USER_ID",
                    context: { type: "user_order_stats" }
                }
            });
        }

        console.log(`getUserOrderStats: userId=${userId}`);

        const result = await orderService.getUserOrderStats(userId);

        if (!result.success) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: result.error,
                    code: result.code,
                    context: { type: "user_order_stats", userId: userId }
                }
            });
        }

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: result.metric_value,
                context: { type: "user_order_stats", context: result.context.context }
            }
        });
    } catch (error) {
        console.error("Error in getUserOrderStats:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: "Failed to retrieve user order statistics",
                code: "SERVER_ERROR",
                context: { type: "user_order_stats" }
            }
        });
    }
}

/**
 * Retrieves the status summary for a specific order by order ID and user ID.
 *
 * Validates the presence of the order ID, fetches the order summary using the backend order service, and returns structured JSON containing order status, total, creation date, estimated delivery, status details, and mixed status flag. Returns an error response if the order ID is missing, the order is not found, or an exception occurs.
 * @returns {Promise<Object>} JSON response with order status information or error details.
 */
export async function get_getOrderStatus(request) {
    try {
        const url = new URL(request.url);
        const orderId = url.searchParams.get("orderId");
        const userId = extractUserId(request);

        if (!orderId) {
            return badRequest({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: "Order ID is required",
                    code: "MISSING_PARAMETER",
                    context: { type: "order_status" }
                }
            });
        }

        const result = await orderService.getOrderSummary(orderId, userId);

        if (!result.success) {
            return ok({
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: {
                    success: false,
                    metric_value: [],
                    error: result.error,
                    code: result.code,
                    context: { type: "order_status", orderId: orderId }
                }
            });
        }

        const orderInfo = {
            orderId: result.metric_value[0]._id,
            status: result.metric_value[0].aggregatedStatus,
            total: result.metric_value[0].total,
            createdDate: result.metric_value[0]._createdDate,
            estimatedDelivery: result.metric_value[0].Estimateddeliverydate || "5-7 business days",
            statusDetails: result.context.statusDetails,
            hasMixedStatus: result.context.hasMixedStatus
        };

        return ok({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: true,
                metric_value: [orderInfo],
                context: { type: "order_status", orderId: orderId }
            }
        });
    } catch (error) {
        console.error("Error in getOrderStatus:", error);
        return badRequest({
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: {
                success: false,
                metric_value: [],
                error: "Failed to retrieve order status",
                code: "SERVER_ERROR",
                context: { type: "order_status" }
            }
        });
    }
}