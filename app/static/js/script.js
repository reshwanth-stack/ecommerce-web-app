
document.addEventListener("DOMContentLoaded", function () {
    console.log("ShopEase application loaded successfully.");

    const addToCartForms = document.querySelectorAll(
        'form[action*="/cart/add/"]'
    );

    addToCartForms.forEach(function (form) {
        form.addEventListener("submit", function () {
            console.log("Adding product to cart...");
        });
    });
});
