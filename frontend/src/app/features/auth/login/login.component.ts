import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="login-container">
      <mat-card class="login-card shadow-card">
        <mat-card-header>
          <div mat-card-avatar class="header-image">
            <mat-icon color="primary">local_shipping</mat-icon>
          </div>
          <mat-card-title>Logistics System</mat-card-title>
          <mat-card-subtitle>Iniciar sesión</mat-card-subtitle>
        </mat-card-header>

        <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
          <mat-card-content class="login-form-content">
            <!-- Error message -->
            <div *ngIf="errorMessage()" class="error-message">
              <mat-icon>error_outline</mat-icon>
              <span>{{ errorMessage() }}</span>
            </div>

            <!-- Username -->
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Usuario</mat-label>
              <input matInput formControlName="username" placeholder="Ingresa tu usuario">
              <mat-error *ngIf="loginForm.get('username')?.hasError('required')">
                El usuario es obligatorio
              </mat-error>
            </mat-form-field>

            <!-- Password -->
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Contraseña</mat-label>
              <input matInput [type]="hidePassword() ? 'password' : 'text'" formControlName="password" placeholder="Ingresa tu contraseña">
              <button mat-icon-button matSuffix (click)="togglePasswordVisibility()" type="button" [attr.aria-label]="'Ocultar contraseña'">
                <mat-icon>{{hidePassword() ? 'visibility_off' : 'visibility'}}</mat-icon>
              </button>
              <mat-error *ngIf="loginForm.get('password')?.hasError('required')">
                La contraseña es obligatoria
              </mat-error>
            </mat-form-field>
          </mat-card-content>

          <mat-card-actions class="login-actions">
            <button mat-flat-button color="primary" type="submit" [disabled]="loginForm.invalid || isLoading()" class="submit-button">
              <mat-spinner diameter="20" *ngIf="isLoading()" class="spinner"></mat-spinner>
              <span *ngIf="!isLoading()">Ingresar</span>
            </button>
          </mat-card-actions>
        </form>
      </mat-card>
    </div>
  `,
  styles: [`
    .login-container {
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      background-color: #f5f7fa;
    }
    .login-card {
      width: 100%;
      max-width: 400px;
      padding: 16px;
    }
    .header-image {
      background-color: rgba(63, 81, 181, 0.1);
      display: flex;
      justify-content: center;
      align-items: center;
      border-radius: 50%;
    }
    mat-card-header {
      margin-bottom: 24px;
    }
    .login-form-content {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .full-width {
      width: 100%;
    }
    .error-message {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px;
      background-color: #ffebee;
      color: #c62828;
      border-radius: 4px;
      margin-bottom: 16px;
      font-size: 14px;
    }
    .login-actions {
      padding: 0 16px 16px 16px;
    }
    .submit-button {
      width: 100%;
      height: 48px;
      font-size: 16px;
    }
    .spinner {
      margin: 0 auto;
    }
  `]
})
export class LoginComponent {
  loginForm: FormGroup;
  isLoading = signal(false);
  errorMessage = signal<string | null>(null);
  hidePassword = signal(true);

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {
    this.loginForm = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required]
    });
  }

  togglePasswordVisibility() {
    this.hidePassword.set(!this.hidePassword());
  }

  onSubmit() {
    if (this.loginForm.invalid) return;

    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.authService.login(this.loginForm.value).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.router.navigate(['/dashboard']);
      },
      error: () => {
        this.isLoading.set(false);
        this.errorMessage.set('Acceso denegado');
      }
    });
  }
}
