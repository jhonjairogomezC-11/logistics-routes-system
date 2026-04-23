import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { catchError } from 'rxjs';
import { throwError } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();

  // Clonar la request para añadir el header Authorization
  let authReq = req;
  if (token) {
    authReq = req.clone({
      setHeaders: {
        Authorization: `Token ${token}`
      }
    });
  }

  return next(authReq).pipe(
    catchError((error) => {
      // Si el backend devuelve 401 Unauthorized, cerramos la sesión localmente
      if (error.status === 401) {
        authService.logout();
      }
      return throwError(() => error);
    })
  );
};
