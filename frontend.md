# Frontend Documentation

This document outlines the frontend structure, assets, and templates created for the AI Trip Planner application, built using Jinja2, Vanilla JavaScript, and CSS.

## Overview

The frontend is designed with a premium aesthetic, prioritizing modern UI trends like glassmorphism, dynamic gradients, smooth micro-animations, and clean typography using the Google 'Outfit' font. It integrates seamlessly with the backend FastAPI architecture.

## File Structure

The frontend components are organized within the `app/` directory as follows:

```
app/
├── templates/
│   ├── base.html
│   ├── signup.html
│   ├── login.html
│   ├── chat.html
│   ├── dashboard.html
│   ├── email_template.html
│   └── partials/
│       └── treasure_map.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── chat.js
```

## Templates

All HTML files are Jinja2 templates. Most extend from a common base to ensure layout consistency.

### `base.html`
- Serves as the primary layout wrapper for the application.
- Includes the `<head>` boilerplate, loads `style.css`, and initializes the Google Fonts.
- Contains the main navigation bar which is designed to dynamically update based on the user's authentication state (handled via Jinja variables like `request.state.user`).

### Authentication
- **`signup.html`**: A clean, centered form allowing new users to register.
- **`login.html`**: The authentication form for returning users. Both utilize the `.glass-panel` utility class for a sleek UI.

### Core Application
- **`chat.html`**: The primary interaction interface where users converse with the AI agent to plan their trips. Features a modern chat UI and a typing indicator to visually signal when the AI is processing requests.
- **`dashboard.html`**: Displays a grid of the user's generated trip plans (as interactive cards). It conditionally renders the `treasure_map.html` partial when a specific trip plan is being viewed.

### Sub-Components & Notifications
- **`partials/treasure_map.html`**: A dynamic, visual representation of a generated itinerary. It renders:
  - An interactive SVG path that connects daily milestones.
  - Absolute positioned pins for different days, which reveal hover popups detailing the day's activities and hotels.
  - A visual budget tracking progress bar at the bottom.
  - Fallback mock data for previewing the map even when an itinerary isn't fully loaded.
- **`email_template.html`**: A dedicated HTML email layout sent out upon itinerary completion. It is styled appropriately for email clients and references a generated PNG version of the treasure map (using `cid:treasure_map_image`).

## Static Assets

### `style.css`
- **Design System**: Defines CSS variables (`--primary`, `--bg-dark`, etc.) to maintain a consistent color palette across the application.
- **Glassmorphism**: Provides the `.glass-panel` utility class using `backdrop-filter` and semi-transparent backgrounds to give depth to the UI.
- **Animations**: Includes keyframes for interactive elements like the chat loading bounce (`@keyframes bounce`), the user message fade-ins (`@keyframes fadeIn`), and the treasure map path drawing (`@keyframes drawPath`).
- **Responsive Elements**: Ensures grid layouts (like the dashboard) and flex containers (like the chat window) are fluid and mobile-friendly.

### `chat.js`
- **Event Handling**: Intercepts the chat form submission to prevent standard page reloads.
- **UI State**: Manages appending user messages to the chat DOM, toggling the display of the typing indicator, and locking the input field during active API calls.
- **API Communication**: Uses the `fetch` API to send the user's query to the backend endpoint.
- **Response Processing**: Parses the JSON response to either:
  - Append the AI's follow-up questions to the chat history.
  - Redirect the user to their dashboard (via `window.location.href`) once the trip planning sequence is completed by the backend graph.
