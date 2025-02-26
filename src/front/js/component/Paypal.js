
import React, { useEffect, useRef } from "react";

export const PayPal = () => {
    const paypalButtonRef = useRef(null);
    const resultMessageRef = useRef(null);

    // Function to display result messages
    const resultMessage = (message) => {
        if (resultMessageRef.current) {
            resultMessageRef.current.innerHTML = message;
        }
    };

    useEffect(() => {
        // Make sure PayPal script is loaded
        if (window.paypal) {
            // Clear any existing buttons
            if (paypalButtonRef.current) {
                paypalButtonRef.current.innerHTML = '';
            }

            // Get the backend URL from environment or use a default with correct port
            const backendUrl = process.env.BACKEND_URL || 'http://localhost:3001';

            window.paypal
                .Buttons({
                    style: {
                        shape: "rect",
                        layout: "vertical",
                        color: "gold",
                        label: "paypal",
                    },
                    message: {
                        amount: 100,
                    },

                    async createOrder() {
                        try {
                            const response = await fetch(`${backendUrl}/api/orders`, {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                // use the "body" param to optionally pass additional order information
                                // like product ids and quantities
                                body: JSON.stringify({
                                    cart: [
                                        {
                                            // id: "YOUR_PRODUCT_ID",
                                            // quantity: "YOUR_PRODUCT_QUANTITY",
                                            id: "5",
                                            quantity: "2",
                                        },
                                    ],
                                }),
                            });

                            const orderData = await response.json();

                            if (orderData.id) {
                                return orderData.id;
                            }
                            const errorDetail = orderData?.details?.[0];
                            const errorMessage = errorDetail
                                ? `${errorDetail.issue} ${errorDetail.description} (${orderData.debug_id})`
                                : JSON.stringify(orderData);

                            throw new Error(errorMessage);
                        } catch (error) {
                            console.error(error);
                            resultMessage(`Could not initiate PayPal Checkout...<br><br>${error}`);
                        }
                    },

                    async onApprove(data, actions) {
                        try {
                            const response = await fetch(
                                `${backendUrl}/api/orders/${data.orderID}/capture`,
                                {
                                    method: "POST",
                                    headers: {
                                        "Content-Type": "application/json",
                                    },
                                }
                            );

                            const orderData = await response.json();
                            // Three cases to handle:
                            //   (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()
                            //   (2) Other non-recoverable errors -> Show a failure message
                            //   (3) Successful transaction -> Show confirmation or thank you message

                            const errorDetail = orderData?.details?.[0];

                            if (errorDetail?.issue === "INSTRUMENT_DECLINED") {
                                // (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()
                                // recoverable state, per
                                // https://developer.paypal.com/docs/checkout/standard/customize/handle-funding-failures/
                                return actions.restart();
                            } else if (errorDetail) {
                                // (2) Other non-recoverable errors -> Show a failure message
                                throw new Error(
                                    `${errorDetail.description} (${orderData.debug_id})`
                                );
                            } else if (!orderData.purchase_units) {
                                throw new Error(JSON.stringify(orderData));
                            } else {
                                // (3) Successful transaction -> Show confirmation or thank you message
                                // Or go to another URL:  actions.redirect('thank_you.html');
                                const transaction =
                                    orderData?.purchase_units?.[0]?.payments
                                        ?.captures?.[0] ||
                                    orderData?.purchase_units?.[0]?.payments
                                        ?.authorizations?.[0];
                                resultMessage(
                                    `Transaction ${transaction.status}: ${transaction.id}<br>
                                     <br>See console for all available details`
                                );
                                console.log(
                                    "Capture result",
                                    orderData,
                                    JSON.stringify(orderData, null, 2)
                                );
                            }
                        } catch (error) {
                            console.error(error);
                            resultMessage(
                                `Sorry, your transaction could not be processed...<br><br>${error}`
                            );
                        }
                    },
                })
                .render(paypalButtonRef.current);
        }
    }, []);

    return (
        <div className="container">
            <div id="paypal-button-container" ref={paypalButtonRef}></div>
            <p id="result-message" ref={resultMessageRef}></p>
        </div>
    );
};






// import React from "react";






// export const PayPal = () => {
//     window.paypal
//         .Buttons({
//             style: {
//                 shape: "rect",
//                 layout: "vertical",
//                 color: "gold",
//                 label: "paypal",
//             },
//             message: {
//                 amount: 100,
//             },

//             async createOrder() {
//                 try {
//                     const response = await fetch(process.env.BACKEND_URL + "/api/orders", {
//                         method: "POST",
//                         headers: {
//                             "Content-Type": "application/json",
//                         },
//                         // use the "body" param to optionally pass additional order information
//                         // like product ids and quantities
//                         body: JSON.stringify({
//                             cart: [
//                                 {
//                                     // id: "YOUR_PRODUCT_ID",
//                                     id: "5",
//                                     // quantity: "YOUR_PRODUCT_QUANTITY",
//                                     quantity: "2",
//                                 },
//                             ],
//                         }),
//                     });

//                     const orderData = await response.json();

//                     if (orderData.id) {
//                         return orderData.id;
//                     }
//                     const errorDetail = orderData?.details?.[0];
//                     const errorMessage = errorDetail
//                         ? `${errorDetail.issue} ${errorDetail.description} (${orderData.debug_id})`
//                         : JSON.stringify(orderData);

//                     throw new Error(errorMessage);
//                 } catch (error) {
//                     console.error(error);
//                     // resultMessage(`Could not initiate PayPal Checkout...<br><br>${error}`);
//                 }
//             },

//             async onApprove(data, actions) {
//                 try {
//                     const response = await fetch(
//                         `/api/orders/${data.orderID}/capture`,
//                         {
//                             method: "POST",
//                             headers: {
//                                 "Content-Type": "application/json",
//                             },
//                         }
//                     );

//                     const orderData = await response.json();
//                     // Three cases to handle:
//                     //   (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()
//                     //   (2) Other non-recoverable errors -> Show a failure message
//                     //   (3) Successful transaction -> Show confirmation or thank you message

//                     const errorDetail = orderData?.details?.[0];

//                     if (errorDetail?.issue === "INSTRUMENT_DECLINED") {
//                         // (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()
//                         // recoverable state, per
//                         // https://developer.paypal.com/docs/checkout/standard/customize/handle-funding-failures/
//                         return actions.restart();
//                     } else if (errorDetail) {
//                         // (2) Other non-recoverable errors -> Show a failure message
//                         throw new Error(
//                             `${errorDetail.description} (${orderData.debug_id})`
//                         );
//                     } else if (!orderData.purchase_units) {
//                         throw new Error(JSON.stringify(orderData));
//                     } else {
//                         // (3) Successful transaction -> Show confirmation or thank you message
//                         // Or go to another URL:  actions.redirect('thank_you.html');
//                         const transaction =
//                             orderData?.purchase_units?.[0]?.payments
//                                 ?.captures?.[0] ||
//                             orderData?.purchase_units?.[0]?.payments
//                                 ?.authorizations?.[0];
//                         resultMessage(
//                             `Transaction ${transaction.status}: ${transaction.id}<br>
//           <br>See console for all available details`
//                         );
//                         console.log(
//                             "Capture result",
//                             orderData,
//                             JSON.stringify(orderData, null, 2)
//                         );
//                     }
//                 } catch (error) {
//                     console.error(error);
//                     resultMessage(
//                         `Sorry, your transaction could not be processed...<br><br>${error}`
//                     );
//                 }
//             },
//         })


//     return (
//         <div className="container">
//             <div id="paypal-button-container"></div>
//             <p id="result-message"></p>
//         </div>
//     )
// }