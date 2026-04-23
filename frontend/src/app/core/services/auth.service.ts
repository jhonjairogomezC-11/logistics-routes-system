import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { BehaviorSubject, Observable, tap, catchError, throwError } from 'rxjs';
import { Router } from '@angular/router';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = `${environment.apiUrl}/auth`;
  
  // Usamos signals para el estado reactivo
  private currentUserSignal = signal<User | null>(null);
  public currentUser = computed(() => this.currentUserSignal());
  public isAuthenticated = computed(() => this.currentUserSignal() !== null);

  constructor(private http: HttpClient, private router: Router) {
    this.checkInitialSession();
  }

  private checkInitialSession() {
    const token = localStorage.getItem('auth_token');
    const userJson = localStorage.getItem('auth_user');
    
    if (token && userJson) {
      try {
        const user = JSON.parse(userJson);
        this.currentUserSignal.set(user);
        // Opcional: verificar token con el backend
        // this.verifySession().subscribe();
      } catch (e) {
        this.logout();
      }
    }
  }

  login(credentials: any): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login/`, credentials).pipe(
      tap(response => {
        localStorage.setItem('auth_token', response.token);
        localStorage.setItem('auth_user', JSON.stringify(response.user));
        this.currentUserSignal.set(response.user);
      })
    );
  }

  logout() {
    // Intentar logout en el backend si hay token, pero borrar estado local de todas formas
    const token = this.getToken();
    if (token) {
      this.http.post(`${this.apiUrl}/logout/`, {}).pipe(
        catchError(() => { return []; }) // Ignorar error si el token ya expiró
      ).subscribe();
    }
    
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    this.currentUserSignal.set(null);
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  verifySession(): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/user/`).pipe(
      tap(user => {
        localStorage.setItem('auth_user', JSON.stringify(user));
        this.currentUserSignal.set(user);
      }),
      catchError(err => {
        this.logout();
        return throwError(() => err);
      })
    );
  }
}
