# Etapa 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código
COPY . .

# Construir la aplicación Angular
RUN npm run build -- --configuration production

# Etapa 2: Serve con Nginx
FROM nginx:alpine

# Eliminar configuración por defecto de nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copiar nuestra configuración personalizada
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar los archivos construidos de Angular al directorio de nginx
# Asegurarse que el nombre de la carpeta coincida con 'outputPath' en angular.json
# Usualmente es dist/frontend/browser o dist/frontend
COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html

EXPOSE 4200

CMD ["nginx", "-g", "daemon off;"]
