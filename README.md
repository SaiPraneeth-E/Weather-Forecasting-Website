# 🌦️ Weather Forecasting Website

![Node.js](https://img.shields.io/badge/Node.js-18.x-green)
![Express.js](https://img.shields.io/badge/Express.js-Backend-blue)
![JavaScript](https://img.shields.io/badge/JavaScript-Frontend-yellow)
![License](https://img.shields.io/badge/License-MIT-brightgreen)

A full-stack **Weather Forecasting Web Application** that provides
real-time weather updates for cities worldwide.\
Built with **Node.js**, **Express.js**, and a dynamic frontend using
**HTML, CSS, and JavaScript**, this project integrates a live weather
API to deliver accurate and up-to-date weather information.

------------------------------------------------------------------------

## 🚀 Live Demo

> [Live Link](https://forecast-x-jru6.onrender.com/)

------------------------------------------------------------------------

## ✨ Key Features

-   🔍 Search weather by city name
-   🌡️ Real-time temperature (°C)
-   🌥️ Weather condition & description
-   💧 Humidity levels
-   🌬️ Wind speed
-   🎨 Dynamic UI updates based on weather conditions
-   📱 Fully responsive design
-   ⚡ API-based live data fetching
-   🔐 Environment variable protection using `.env`

------------------------------------------------------------------------

## 🧠 Tech Stack

### 🔹 Frontend

-   HTML5
-   CSS3
-   JavaScript (Vanilla JS)

### 🔹 Backend

-   Node.js
-   Express.js

### 🔹 API

-   OpenWeatherMap API

------------------------------------------------------------------------

## 📁 Project Structure

    Weather-Forecasting-Website/
    │
    ├── public/
    │   ├── css/
    │   ├── js/
    │   └── assets/
    │
    ├── views/
    │   └── index.ejs
    │
    ├── app.js
    ├── package.json
    ├── .env
    └── README.md

------------------------------------------------------------------------

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

``` bash
git clone https://github.com/SaiPraneeth-E/Weather-Forecasting-Website.git
cd Weather-Forecasting-Website
```

### 2️⃣ Install Dependencies

``` bash
npm install
```

### 3️⃣ Configure Environment Variables

Create a `.env` file in the root directory:

    API_KEY=YOUR_OPENWEATHER_API_KEY
    PORT=3000

Get your free API key from: https://openweathermap.org/api

### 4️⃣ Start the Server

``` bash
npm start
```

### 5️⃣ Open in Browser

    http://localhost:3000

------------------------------------------------------------------------

## 🔗 API Endpoint Example

    https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric

------------------------------------------------------------------------

## 📸 Screenshots (Add Your Images)

Create a folder named `screenshots/` and add:

``` markdown
![Home Page](./screenshots/home.png)
![Weather Results](./screenshots/result.png)
```

------------------------------------------------------------------------

## 📈 Future Enhancements

-   🌍 7-Day Forecast Feature
-   📍 Geolocation-Based Weather Detection
-   🌙 Dark/Light Mode Toggle
-   🕘 Search History
-   📊 Weather Data Charts
-   🗄️ Database Integration for Saved Cities

------------------------------------------------------------------------

## 🤝 Contributing

Contributions are welcome!

1.  Fork the repository
2.  Create your feature branch (`git checkout -b feature-name`)
3.  Commit your changes (`git commit -m 'Add feature'`)
4.  Push to the branch (`git push origin feature-name`)
5.  Open a Pull Request

------------------------------------------------------------------------

## 👨‍💻 Author

**EDUPULAPATI SAI PRANEETH**\
AI/ML & Software Engineer\
GitHub: https://github.com/SaiPraneeth-E

------------------------------------------------------------------------

## 📄 License

This project is licensed under the MIT License.

------------------------------------------------------------------------

⭐ If you found this project helpful, please consider giving it a star!
