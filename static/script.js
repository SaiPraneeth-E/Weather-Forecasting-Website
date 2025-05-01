// --- DOM ELEMENTS (Updated to match new HTML) ---
const cityInput = document.getElementById('cityInput');
const searchBtn = document.getElementById('searchBtn');
const loader = document.getElementById('loader');
const errorMessageDiv = document.getElementById('errorMessage');
const weatherResultsDiv = document.getElementById('weather-results');
const locationNameH3 = document.getElementById('locationName');
// Current Weather Elements
const currentIcon = document.getElementById('currentIcon');
const currentTemp = document.getElementById('currentTemp');
const currentDesc = document.getElementById('currentDesc');
const currentFeelsLike = document.getElementById('currentFeelsLike'); // Now in highlights
const currentDateSpan = document.getElementById('currentDate'); // Added for date
// Highlight Card Elements
const detailHumidity = document.getElementById('detailHumidity');
const detailPressure = document.getElementById('detailPressure');
const detailWind = document.getElementById('detailWind');
const detailVisibility = document.getElementById('detailVisibility');
const currentSunrise = document.getElementById('currentSunrise'); // For highlight card
const currentSunset = document.getElementById('currentSunset');   // For highlight card
// Forecast Containers
const dailyForecastList = document.getElementById('dailyForecastList'); // Changed to UL
// Air Pollution
const aqiValueSpan = document.getElementById('aqiValue');
const aqiDescSpan = document.getElementById('aqiDesc');
const airComponentsDiv = document.getElementById('airComponents');
// Map Elements (Now Active)
const mapDiv = document.getElementById('map');
const mapLayerSelect = document.getElementById('mapLayerSelect');
// Chart Elements (New)
const hourlyTempChartCanvas = document.getElementById('hourlyTempChart');


// --- API & Map Configuration ---
// const MAP_API_KEY = Passed from Flask template
// const API_BASE_URL = Passed from Flask template

// --- Map & Chart Variables (Global Scope) ---
let map = null;
let owmTileLayer = null;
let hourlyChart = null;


// --- HELPER FUNCTIONS (Keep these as they are useful) ---
const mpsToKmh = (mps) => (mps * 3.6).toFixed(1);
const formatTime = (timestamp, timezoneOffsetSeconds) => {
    const date = new Date((timestamp + timezoneOffsetSeconds) * 1000);
    // Use local time formatting based on user's browser settings but calculated from UTC + offset
    const options = { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'UTC' };
     // Use a more robust way to get local HH:MM format based on UTC+offset
    const localDate = new Date(date.getTime()); // Use the UTC timestamp
    // Format using Intl ensuring we force the timeZone to UTC first, then let browser format
    try {
        return new Intl.DateTimeFormat([], {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: 'UTC' // Calculate based on UTC
        }).format(localDate);
        // Alternative: Use browser default locale with calculated time
        // const offsetMs = timezoneOffsetSeconds * 1000;
        // const localTime = new Date(timestamp * 1000 + offsetMs);
        // return localTime.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', hour12: false});
    } catch (e) {
        // Fallback to UTC display if locale fails
         console.warn("toLocaleTimeString with specific timezone failed, falling back.", e);
        return date.toLocaleTimeString('en-GB', options); // Use 'en-GB' for HH:MM
    }
};
const formatDate = (timestamp, timezoneOffsetSeconds, format = 'short') => {
    const date = new Date((timestamp + timezoneOffsetSeconds) * 1000);
    if (format === 'full') {
        // Format to Weekday, Month Day, Year in UTC
        return date.toLocaleDateString('en-US', { timeZone: 'UTC', weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    }
    // Default short format: Day, Mon ##
    return date.toLocaleDateString('en-US', { timeZone: 'UTC', weekday: 'short', month: 'short', day: 'numeric' });
};
const getWindDirection = (deg) => {
    if (deg === undefined || deg === null) return '';
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    const index = Math.round(deg / 22.5) % 16;
    return directions[index];
};
const getAqiDescription = (aqi) => {
    switch (aqi) {
        case 1: return 'Good'; case 2: return 'Fair'; case 3: return 'Moderate';
        case 4: return 'Poor'; case 5: return 'Very Poor'; default: return 'N/A';
    }
};
const showError = (message) => {
    errorMessageDiv.textContent = message; errorMessageDiv.style.display = 'block'; weatherResultsDiv.style.display = 'none';
};
const clearError = () => { errorMessageDiv.style.display = 'none'; errorMessageDiv.textContent = ''; }
const showLoader = (isLoading) => { loader.style.display = isLoading ? 'block' : 'none'; };

// --- FETCH WEATHER BUNDLE FROM BACKEND (Keep as before) ---
const fetchWeatherBundle = async (cityName) => {
    const url = `${API_BASE_URL}/weather_bundle?city=${encodeURIComponent(cityName)}`;
    try {
        const response = await fetch(url);
        if (!response.ok) {
             let errorData; try { errorData = await response.json(); } catch (e) { /* ignore */ }
             const message = errorData?.error || `Error ${response.status}: ${response.statusText}`;
             if (response.status === 401 || response.redirected) { throw new Error("Unauthorized. Session may have expired. Please log in again."); }
            throw new Error(message);
        }
        return await response.json();
    } catch (error) { console.error('Error fetching weather bundle:', error); throw error; }
};

// --- DISPLAY FUNCTIONS ---

function displayCurrentWeatherAndHighlights(currentData, locationData, timezoneOffset) {
    const { main, weather, wind, sys, visibility, name } = currentData;

    // Update location title
    locationNameH3.textContent = `${locationData.name}, ${locationData.country}`;

    // Update "Now" Card
    currentTemp.textContent = `${Math.round(main.temp)}°C`;
    currentIcon.src = `https://openweathermap.org/img/wn/${weather[0].icon}@2x.png`;
    currentIcon.alt = weather[0].description;
    currentDesc.textContent = weather[0].description;
    currentDateSpan.textContent = formatDate(currentData.dt, timezoneOffset, 'full'); // Show full date

    // Update Highlights
    currentFeelsLike.textContent = `${Math.round(main.feels_like)}°C`;
    detailHumidity.textContent = `${main.humidity} %`;
    detailPressure.textContent = `${main.pressure} hPa`;
    detailVisibility.textContent = `${(visibility / 1000).toFixed(1)} km`;
    const windDir = getWindDirection(wind?.deg); // Add safe navigation for wind.deg
    const windSpeed = wind?.speed !== undefined ? mpsToKmh(wind.speed) : '-';
    detailWind.textContent = windDir ? `${windSpeed} km/h (${windDir})` : `${windSpeed} km/h`;
    currentSunrise.textContent = formatTime(sys.sunrise, timezoneOffset);
    currentSunset.textContent = formatTime(sys.sunset, timezoneOffset);
}

function displayAirPollution(airData) {
    // Keep this function mostly as before, but maybe simplify component display
    if (!airData || !airData.list || airData.list.length === 0) {
        aqiValueSpan.textContent = 'N/A'; aqiDescSpan.textContent = '';
        airComponentsDiv.innerHTML = '<span>N/A</span>';
        return;
    }
    const aqi = airData.list[0].main.aqi;
    const components = airData.list[0].components;
    aqiValueSpan.textContent = aqi;
    aqiDescSpan.textContent = getAqiDescription(aqi);

    // Compact display for components
    airComponentsDiv.innerHTML = `
        <span>PM2.5: ${components.pm2_5?.toFixed(1) ?? '-'}</span>
        <span>SO2: ${components.so2?.toFixed(1) ?? '-'}</span>
        <span>NO2: ${components.no2?.toFixed(1) ?? '-'}</span>
        <span>O3: ${components.o3?.toFixed(1) ?? '-'}</span>
    `; // Added nullish coalescing for safety
}

function displayDailyForecast(forecastList, timezoneOffsetSeconds) {
    dailyForecastList.innerHTML = ''; // Clear previous list items or placeholders
    const dailyData = {};

    // Group forecast items by day
    forecastList.forEach(item => {
        const dateStr = formatDate(item.dt, timezoneOffsetSeconds); // Use short format for key
         if (!dailyData[dateStr]) {
             dailyData[dateStr] = { temps: [], pops: [], icons: [], descs: [], dt: item.dt };
         }
         dailyData[dateStr].temps.push(item.main.temp);
         dailyData[dateStr].pops.push(item.pop); // Probability of precipitation
         // Store first icon/desc found for the day, maybe prioritize non-clear later if needed
         if (!dailyData[dateStr].icons.length) {
            dailyData[dateStr].icons.push(item.weather[0].icon);
            dailyData[dateStr].descs.push(item.weather[0].description);
         }
    });

    // Create forecast list items for the next 5 days
    const sortedDays = Object.entries(dailyData).sort((a, b) => a[1].dt - b[1].dt);

    sortedDays.slice(0, 5).forEach(([dateStr, dayData]) => {
        const maxTemp = Math.round(Math.max(...dayData.temps));
        const minTemp = Math.round(Math.min(...dayData.temps));
        const icon = dayData.icons[0] || '01d';

        const listItem = document.createElement('li');
        listItem.classList.add('forecast-list-item');
        listItem.innerHTML = `
            <span>${dateStr.split(', ')[0]}</span> <!-- Just show day -->
            <img src="https://openweathermap.org/img/wn/${icon}.png" alt="-">
            <span>${maxTemp}°/${minTemp}°C</span>
        `;
        dailyForecastList.appendChild(listItem);
    });
}

// --- HOURLY FORECAST CHART FUNCTION (NEW) ---
function displayHourlyForecastChart(forecastList, timezoneOffsetSeconds) {
    if (!hourlyTempChartCanvas) return; // Exit if canvas element doesn't exist
    const ctx = hourlyTempChartCanvas.getContext('2d');

    // Destroy previous chart instance if it exists
    if (hourlyChart) {
        hourlyChart.destroy();
        hourlyChart = null; // Reset variable
    }

    // Get data for the next 24 hours (8 intervals of 3 hours)
    const hourlyData = forecastList.slice(0, 8);
    const labels = hourlyData.map(item => formatTime(item.dt, timezoneOffsetSeconds));
    const temps = hourlyData.map(item => Math.round(item.main.temp));

    // Chart.js configuration
    hourlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Temperature (°C)',
                data: temps,
                borderColor: 'var(--primary-color)', // Use CSS variable
                backgroundColor: 'rgba(135, 206, 235, 0.2)', // Sky blue with transparency
                borderWidth: 2,
                pointBackgroundColor: 'var(--primary-color)',
                pointBorderColor: '#fff',
                pointHoverRadius: 6,
                pointRadius: 4,
                tension: 0.3, // Slight curve to the line
                fill: true // Fill area under the line
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // Allow chart to fill container height
            scales: {
                y: {
                    beginAtZero: false, // Don't force y-axis to start at 0
                    ticks: {
                        color: 'var(--text-muted-color)', // Use CSS variable
                        callback: function(value) { return value + '°C'; } // Add °C suffix
                    },
                    grid: {
                        color: 'var(--border-color)' // Grid line color
                    }
                },
                x: {
                    ticks: {
                        color: 'var(--text-muted-color)' // Use CSS variable
                    },
                    grid: {
                        color: 'var(--border-color)' // Grid line color
                    }
                }
            },
            plugins: {
                legend: {
                    display: false // Hide legend as it's obvious
                },
                tooltip: {
                    backgroundColor: 'var(--card-bg-color)',
                    titleColor: 'var(--primary-color)',
                    bodyColor: 'var(--text-color)',
                    borderColor: 'var(--border-color)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return ` Temp: ${context.parsed.y}°C`;
                        }
                    }
                }
            }
        }
    });
}


// --- MAP FUNCTIONS (NOW ACTIVE) ---
function initializeMap(lat, lon) {
    if (!mapDiv) return; // Exit if map div doesn't exist
    if (map) { // If map already exists, just update view and layer
        updateMapViewAndLayer(lat, lon);
        return;
    }

    // Create map instance if it doesn't exist
    map = L.map(mapDiv).setView([lat, lon], 10); // Initial zoom level 10

    // Add base tile layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
    }).addTo(map);

    // Add initial weather layer (e.g., temperature)
    updateMapLayer(); // Call this to add the default selected layer
}

function updateMapLayer() {
    if (!map || !mapLayerSelect || !MAP_API_KEY) return; // Ensure map, select, and key exist

    const selectedLayer = mapLayerSelect.value;
    const owmLayerUrl = `https://tile.openweathermap.org/map/${selectedLayer}/{z}/{x}/{y}.png?appid=${MAP_API_KEY}`;

    // Remove the previous OWM layer if it exists
    if (owmTileLayer) {
        map.removeLayer(owmTileLayer);
    }

    // Add the new OWM layer
    owmTileLayer = L.tileLayer(owmLayerUrl, {
        attribution: '© <a href="https://openweathermap.org/">OpenWeatherMap</a>',
        opacity: 0.7 // Adjust transparency
    });
    owmTileLayer.addTo(map);
}

// Helper to update map view and ensure the current layer is shown
function updateMapViewAndLayer(lat, lon) {
    if (!map) return;
    map.setView([lat, lon], 10); // Update center and zoom
    updateMapLayer(); // Re-apply the currently selected layer
}


// --- MAIN SEARCH HANDLER ---
async function handleSearch() {
    const city = cityInput.value.trim();
    if (!city) { showError('Please enter a city name.'); return; }

    showLoader(true); clearError(); weatherResultsDiv.style.display = 'none';

    try {
        const bundle = await fetchWeatherBundle(city);
        const timezoneOffset = bundle.current.timezone; // Get offset from current data

        // Update display functions
        displayCurrentWeatherAndHighlights(bundle.current, bundle.location, timezoneOffset);
        displayAirPollution(bundle.air_pollution);
        displayDailyForecast(bundle.forecast.list, timezoneOffset);
        displayHourlyForecastChart(bundle.forecast.list, timezoneOffset); // Call chart function

        // Initialize or update map
        initializeMap(bundle.location.lat, bundle.location.lon);

        weatherResultsDiv.style.display = 'block';

    } catch (error) {
        console.error('Search failed:', error);
        showError(error.message || 'An unknown error occurred.');
        if (error.message.toLowerCase().includes("unauthorized")) {
            setTimeout(() => { window.location.href = '/login'; }, 3000);
        }
    } finally {
        showLoader(false);
    }
}

// --- EVENT LISTENERS ---
document.addEventListener('DOMContentLoaded', () => {
    if (searchBtn) { searchBtn.addEventListener('click', handleSearch); }
    if (cityInput) { cityInput.addEventListener('keypress', (event) => { if (event.key === 'Enter') handleSearch(); }); }

    // Map layer selector listener (Now Active)
    if (mapLayerSelect) {
        mapLayerSelect.addEventListener('change', () => {
            if (map) { // Only update if map is initialized
                updateMapLayer();
            }
        });
    }

     // Update Footer Year (Keep this)
     const footer = document.querySelector('footer p');
     if (footer) {
        const currentYear = new Date().getFullYear();
        // Use textContent for safety unless HTML is intended
        footer.textContent = `© ${currentYear} WeatherWise App. Weather data by OpenWeatherMap.`;
     }

    // Clear flash messages after a delay
     setTimeout(() => {
        const alerts = document.querySelectorAll('.flash-container .alert');
        alerts.forEach(alert => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500); // Remove from DOM after fade
        });
    }, 5000); // Adjust delay as needed (5 seconds)
});