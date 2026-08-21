document.addEventListener("DOMContentLoaded", function () {

    const countrySelect = document.getElementById("country-code");

    if (!countrySelect) {
        return;
    }

    fetch("https://ipapi.co/json/")
        .then(response => response.json())
        .then(data => {

            const countryCode = data.country_code;

            if (!countryCode) {
                return;
            }

            const option = countrySelect.querySelector(
                `option[data-country="${countryCode}"]`
            );

            if (option) {
                countrySelect.value = option.value;
            }

        })
        .catch(error => {
            console.log("Country detection unavailable.");
        });

});