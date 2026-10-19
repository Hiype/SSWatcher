FROM nginx:1.27-alpine

# Copy website files
COPY index.html /usr/share/nginx/html/index.html

# Copy OneSignal service worker to web root (required by OneSignal)
COPY OneSignalSDKWorker.js /usr/share/nginx/html/OneSignalSDKWorker.js

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

