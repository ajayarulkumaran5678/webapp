class WeatherDashboard {
    constructor() {
        this.cityInput = document.getElementById('cityInput');
        this.searchBtn = document.getElementById('searchBtn');
        this.suggestions = document.getElementById('suggestions');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.weatherContent = document.getElementById('weatherContent');
        this.errorMessage = document.getElementById('errorMessage');
        
        this.initializeEventListeners();
        this.loadDefaultCity();
    }

    initializeEventListeners() {
        this.searchBtn.addEventListener('click', () => this.searchWeather());
        this.cityInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchWeather();
            }
        });
        
        this.cityInput.addEventListener('input', (e) => {
            this.handleInputChange(e.target.value);
        });
        
        document.addEventListener('click', (e) => {
            if (!this.cityInput.contains(e.target) && !this.suggestions.contains(e.target)) {
                this.suggestions.style.display = 'none';
            }
        });
    }

    async handleInputChange(query) {
        if (query.length < 2) {
            this.suggestions.style.display = 'none';
            return;
        }

        try {
            const response = await fetch(`/search-suggestions/${query}`);
            const suggestions = await response.json();
            this.displaySuggestions(suggestions);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
        }
    }

    displaySuggestions(suggestions) {
        if (suggestions.length === 0) {
            this.suggestions.style.display = 'none';
            return;
        }

        this.suggestions.innerHTML = suggestions.map(city => 
            `<div class="suggestion-item" onclick="weatherApp.selectSuggestion('${city}')">${city}</div>`
        ).join('');
        
        this.suggestions.style.display = 'block';
    }

    selectSuggestion(city) {
        this.cityInput.value = city;
        this.suggestions.style.display = 'none';
        this.searchWeather();
    }

    async searchWeather() {
        const city = this.cityInput.value.trim();
        if (!city) return;

        this.showLoading();
        this.hideError();

        try {
            const response = await fetch(`/weather/${encodeURIComponent(city)}`);
            const data = await response.json();

            if (response.ok) {
                this.displayWeather(data);
                this.hideLoading();
                this.showWeatherContent();
            } else {
                throw new Error(data.error || 'Weather data not found');
            }
        } catch (error) {
            console.error('Error fetching weather:', error);
            this.hideLoading();
            this.showError();
        }
    }

    displayWeather(data) {
        // Update main weather info
        document.getElementById('cityName').textContent = `${data.city}, ${data.country}`;
        document.getElementById('temperature').textContent = data.temperature;
        document.getElementById('description').textContent = data.description;
        document.getElementById('feelsLike').textContent = data.feels_like;
        document.getElementById('weatherIcon').src = `https://openweathermap.org/img/wn/${data.icon}@2x.png`;
        document.getElementById('weatherIcon').alt = data.description;

        // Update stats
        document.getElementById('humidity').textContent = `${data.humidity}%`;
        document.getElementById('windSpeed').textContent = `${data.wind_speed} m/s`;
        document.getElementById('pressure').textContent = `${data.pressure} hPa`;
        document.getElementById('visibility').textContent = `${data.visibility} km`;

        // Update sun times
        document.getElementById('sunrise').textContent = data.sunrise;
        document.getElementById('sunset').textContent = data.sunset;

        // Update forecast
        this.displayForecast(data.forecast);
    }

    displayForecast(forecast) {
        const container = document.getElementById('forecastContainer');
        container.innerHTML = forecast.map(day => `
            <div class="forecast-card">
                <div class="forecast-date">${day.date}</div>
                <img src="https://openweathermap.org/img/wn/${day.icon}@2x.png" alt="${day.description}">
                <div class="forecast-temps">${day.temp_max}° / ${day.temp_min}°</div>
                <div class="forecast-desc">${day.description}</div>
            </div>
        `).join('');
    }

    loadDefaultCity() {
        this.cityInput.value = 'London';
        this.searchWeather();
    }

    showLoading() {
        this.loadingSpinner.style.display = 'block';
        this.weatherContent.style.display = 'none';
        this.errorMessage.style.display = 'none';
    }

    hideLoading() {
        this.loadingSpinner.style.display = 'none';
    }

    showWeatherContent() {
        this.weatherContent.style.display = 'block';
    }

    showError() {
        this.errorMessage.style.display = 'block';
        this.weatherContent.style.display = 'none';
    }

    hideError() {
        this.errorMessage.style.display = 'none';
    }
}

// Initialize the weather dashboard when the page loads
const weatherApp = new WeatherDashboard();