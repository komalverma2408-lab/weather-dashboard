/* =========================================
   ELEMENTS
========================================= */

const cityInput = document.getElementById("cityInput");
const searchBtn = document.getElementById("searchBtn");
const unitToggle = document.getElementById("unitToggle");

const cityName = document.getElementById("cityName");
const temperature = document.getElementById("temperature");
const humidity = document.getElementById("humidity");
const wind = document.getElementById("wind");
const weatherCondition = document.getElementById("weatherCondition");

let currentTemperatureC = null;
let temperatureChart = null;


/* =========================================
   SEARCH WEATHER
========================================= */

async function searchWeather() {

    const city = cityInput.value.trim();

    if (city === "") {
        alert("Please enter a city name");
        return;
    }

    try {

        searchBtn.textContent = "Searching...";
        searchBtn.disabled = true;

        const response = await fetch(
            `http://127.0.0.1:8000/weather?city=${encodeURIComponent(city)}`
        );

        const data = await response.json();

        /* Handle city not found */
        if (data.error) {
            alert(data.error);
            return;
        }

        if (!response.ok) {
            alert(data.detail || "Weather data not found");
            return;
        }


        /* =================================
           UPDATE MAIN WEATHER CARD
        ================================= */

        cityName.textContent = data.city;

        currentTemperatureC = data.temperature;

        temperature.textContent =
            `${Number(data.temperature).toFixed(1)}°C`;

        humidity.textContent =
            `${data.humidity}%`;

        wind.textContent =
            `${data.wind_speed} km/h`;


        /* =================================
           WEATHER CONDITION
        ================================= */

        const weatherInfo =
            getWeatherInfo(data.weather_code);

        weatherCondition.textContent =
            `${weatherInfo.icon} ${weatherInfo.condition}`;


        /* =================================
           WEATHER THEME
        ================================= */

        updateWeatherTheme(weatherInfo.condition);


        /* =================================
           LOAD FORECAST
        ================================= */

        await loadForecast(city);


        /* =================================
           REFRESH SEARCH HISTORY
        ================================= */

        await loadSearchHistory();

    } catch (error) {

        console.log("Weather error:", error);

        alert(
            "Backend server is not running. Please start the FastAPI server."
        );

    } finally {

        searchBtn.textContent = "Search";
        searchBtn.disabled = false;

    }
}


/* =========================================
   WEATHER INFORMATION
========================================= */

function getWeatherInfo(code) {

    if (code === 0) {

        return {
            icon: "☀️",
            condition: "Clear Sky"
        };

    } else if (code <= 3) {

        return {
            icon: "⛅",
            condition: "Partly Cloudy"
        };

    } else if (code === 45 || code === 48) {

        return {
            icon: "🌫️",
            condition: "Foggy"
        };

    } else if (code <= 57) {

        return {
            icon: "🌦️",
            condition: "Drizzle"
        };

    } else if (code <= 67) {

        return {
            icon: "🌧️",
            condition: "Rain"
        };

    } else if (code <= 77) {

        return {
            icon: "❄️",
            condition: "Snow"
        };

    } else if (code <= 82) {

        return {
            icon: "🌦️",
            condition: "Rain Showers"
        };

    } else if (code <= 86) {

        return {
            icon: "🌨️",
            condition: "Snow Showers"
        };

    } else {

        return {
            icon: "⛈️",
            condition: "Thunderstorm"
        };

    }
}


/* =========================================
   WEATHER BASED THEME
========================================= */

function updateWeatherTheme(condition) {

    document.body.classList.remove(
        "theme-clear",
        "theme-cloudy",
        "theme-rain",
        "theme-snow",
        "theme-storm"
    );


    if (condition.includes("Clear")) {

        document.body.classList.add("theme-clear");

    } else if (condition.includes("Cloud")) {

        document.body.classList.add("theme-cloudy");

    } else if (condition.includes("Rain") ||
               condition.includes("Drizzle")) {

        document.body.classList.add("theme-rain");

    } else if (condition.includes("Snow")) {

        document.body.classList.add("theme-snow");

    } else if (condition.includes("Thunderstorm")) {

        document.body.classList.add("theme-storm");

    }

}


/* =========================================
   LOAD 5-DAY FORECAST
========================================= */

async function loadForecast(city) {

    try {

        const response = await fetch(
            `http://127.0.0.1:8000/forecast/${encodeURIComponent(city)}`
        );

        const data = await response.json();


        if (data.error) {

            console.log(data.error);
            return;

        }


        const forecastContainer =
            document.getElementById("forecast-container");

        forecastContainer.innerHTML = "";


        /* =================================
           CREATE FORECAST CARDS
        ================================= */

        for (let i = 0; i < data.dates.length; i++) {

            /*
             * Adding T12:00:00 prevents the
             * date from shifting because of
             * timezone conversion.
             */

            const date =
                new Date(`${data.dates[i]}T12:00:00`);


            const dayName =
                date.toLocaleDateString("en-IN", {
                    weekday: "short"
                });


            const card =
                document.createElement("div");

            card.className = "forecast-card";


            const weatherInfo =
                getWeatherInfo(data.weather_code[i]);


            card.innerHTML = `
                <h3>${dayName}</h3>

                <p class="forecast-date">
                    ${data.dates[i]}
                </p>

                <div class="forecast-icon">
                    ${weatherInfo.icon}
                </div>

                <p class="forecast-condition">
                    ${weatherInfo.condition}
                </p>

                <p class="forecast-temp">
                    ${Math.round(data.max_temperature[i])}°C
                </p>

                <p class="forecast-min">
                    ${Math.round(data.min_temperature[i])}°C
                </p>
            `;


            forecastContainer.appendChild(card);

        }


        /* =================================
           UPDATE TEMPERATURE CHART
        ================================= */

        updateTemperatureChart(data);

    } catch (error) {

        console.log("Forecast error:", error);

    }

}


/* =========================================
   TEMPERATURE CHART
========================================= */

function updateTemperatureChart(data) {

    const canvas =
        document.getElementById("temperatureChart");


    if (!canvas) {
        return;
    }


    /*
     * Destroy old chart before creating
     * a new one.
     */

    if (temperatureChart) {

        temperatureChart.destroy();

    }


    /* =================================
       CREATE DAY LABELS
    ================================= */

    const labels = data.dates.map(date => {

        const day =
            new Date(`${date}T12:00:00`);

        return day.toLocaleDateString("en-IN", {
            weekday: "short"
        });

    });


    /* =================================
       CREATE CHART
    ================================= */

    temperatureChart = new Chart(canvas, {

        type: "line",

        data: {

            labels: labels,

            datasets: [

                {
                    label: "Max Temperature",

                    data: data.max_temperature,

                    borderColor: "#ff7a18",

                    backgroundColor:
                        "rgba(255, 122, 24, 0.15)",

                    borderWidth: 3,

                    pointRadius: 5,

                    pointHoverRadius: 7,

                    tension: 0.4,

                    fill: true
                },


                {
                    label: "Min Temperature",

                    data: data.min_temperature,

                    borderColor: "#2196f3",

                    backgroundColor:
                        "rgba(33, 150, 243, 0.10)",

                    borderWidth: 3,

                    pointRadius: 5,

                    pointHoverRadius: 7,

                    tension: 0.4,

                    fill: true
                }

            ]

        },


        options: {

            responsive: true,

            maintainAspectRatio: false,


            plugins: {

                legend: {
                    display: true
                }

            },


            scales: {

                y: {

                    beginAtZero: false,

                    title: {
                        display: true,
                        text: "Temperature (°C)"
                    }

                }

            }

        }

    });

}


/* =========================================
   SEARCH BUTTON
========================================= */

searchBtn.addEventListener(
    "click",
    searchWeather
);


/* =========================================
   ENTER KEY SEARCH
========================================= */

cityInput.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Enter") {

            searchWeather();

        }

    }
);


/* =========================================
   DATE / TIME / GREETING
========================================= */

function updateDateTime() {

    const now = new Date();

    const hour = now.getHours();

    let greeting;


    if (hour < 12) {

        greeting = "Good Morning 🌅";

    } else if (hour < 17) {

        greeting = "Good Afternoon ☀️";

    } else if (hour < 21) {

        greeting = "Good Evening 🌆";

    } else {

        greeting = "Good Night 🌙";

    }


    document.getElementById(
        "greeting"
    ).textContent = greeting;


    document.getElementById(
        "currentDate"
    ).textContent =

        now.toLocaleDateString("en-IN", {

            weekday: "long",

            day: "numeric",

            month: "long",

            year: "numeric"

        });


    document.getElementById(
        "currentTime"
    ).textContent =

        now.toLocaleTimeString("en-IN", {

            hour: "2-digit",

            minute: "2-digit",

            second: "2-digit"

        });

}


/* Start date/time */

updateDateTime();


/* Update every second */

setInterval(
    updateDateTime,
    1000
);


/* =========================================
   CELSIUS / FAHRENHEIT TOGGLE
========================================= */

unitToggle.addEventListener(
    "click",
    function () {

        if (currentTemperatureC === null) {

            return;

        }


        if (unitToggle.textContent === "°F") {

            const fahrenheit =
                (currentTemperatureC * 9 / 5) + 32;


            temperature.textContent =
                `${fahrenheit.toFixed(1)}°F`;


            unitToggle.textContent = "°C";

        } else {

            temperature.textContent =
                `${currentTemperatureC.toFixed(1)}°C`;


            unitToggle.textContent = "°F";

        }

    }
);


/* =========================================
   LOAD SEARCH HISTORY
========================================= */

async function loadSearchHistory() {

    try {

        const response =
            await fetch(
                "http://127.0.0.1:8000/history"
            );


        const history =
            await response.json();


        const historyContainer =
            document.getElementById(
                "history-container"
            );


        historyContainer.innerHTML = "";


        /* No searches */

        if (history.length === 0) {

            historyContainer.innerHTML =
                "<p>No recent searches yet.</p>";

            return;

        }


        /* Create history cards */

        history.forEach(item => {

            const card =
                document.createElement("div");


            card.className =
                "history-card";


            card.innerHTML = `

                <span>
                    📍 ${item.city}
                </span>

                <small>
                    ${item.country || ""}
                </small>

            `;


            historyContainer.appendChild(card);

        });


    } catch (error) {

        console.log(
            "History error:",
            error
        );

    }

}


/* =========================================
   INITIAL HISTORY LOAD
========================================= */

loadSearchHistory();