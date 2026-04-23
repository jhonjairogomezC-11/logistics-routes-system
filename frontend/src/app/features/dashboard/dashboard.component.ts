// src/app/features/dashboard/dashboard.component.ts
import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { RouteService } from '../../core/services/route.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatProgressBarModule],
  template: `
    <div class="header-section">
      <h1>Dashboard Operativo</h1>
      <p class="subtitle">Resumen general del estado de las rutas logísticas.</p>
    </div>

    <mat-progress-bar *ngIf="loading()" mode="indeterminate" class="mb-4"></mat-progress-bar>

    <div class="stats-grid">
      <!-- TARJETA TOTAL -->
      <mat-card class="stat-card shadow-card total-card">
        <mat-card-header>
          <div mat-card-avatar class="avatar total"><mat-icon>inventory_2</mat-icon></div>
          <mat-card-title>Total Rutas</mat-card-title>
          <mat-card-subtitle>Cargadas en sistema</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <p class="stat-value">{{ stats().total }}</p>
        </mat-card-content>
      </mat-card>

      <!-- TARJETA PREPARADAS -->
      <mat-card class="stat-card shadow-card">
        <mat-card-header>
          <div mat-card-avatar class="avatar ready"><mat-icon>schedule</mat-icon></div>
          <mat-card-title>Rutas Preparadas</mat-card-title>
          <mat-card-subtitle>Listas para ejecución</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <p class="stat-value">{{ stats().ready }}</p>
        </mat-card-content>
      </mat-card>

      <!-- TARJETA PENDIENTES -->
      <mat-card class="stat-card shadow-card">
        <mat-card-header>
          <div mat-card-avatar class="avatar pending"><mat-icon>hourglass_empty</mat-icon></div>
          <mat-card-title>Rutas Pendientes</mat-card-title>
          <mat-card-subtitle>En espera de proceso</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <p class="stat-value">{{ stats().pending }}</p>
        </mat-card-content>
      </mat-card>

      <!-- TARJETA EJECUTADAS -->
      <mat-card class="stat-card shadow-card">
        <mat-card-header>
          <div mat-card-avatar class="avatar executed"><mat-icon>check_circle</mat-icon></div>
          <mat-card-title>Rutas Ejecutadas</mat-card-title>
          <mat-card-subtitle>Finalizadas con éxito</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <p class="stat-value">{{ stats().executed }}</p>
        </mat-card-content>
      </mat-card>

      <!-- TARJETA FALLIDAS -->
      <mat-card class="stat-card shadow-card">
        <mat-card-header>
          <div mat-card-avatar class="avatar failed"><mat-icon>error</mat-icon></div>
          <mat-card-title>Rutas Fallidas</mat-card-title>
          <mat-card-subtitle>Requieren atención</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <p class="stat-value">{{ stats().failed }}</p>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .header-section { margin-bottom: 32px; }
    h1 { margin: 0; color: #333; font-weight: 500; }
    .subtitle { color: #666; margin-top: 4px; }
    .mb-4 { margin-bottom: 24px; }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 24px;
    }
    .stat-card { padding: 8px; border-top: 4px solid #ddd; }
    .stat-value { font-size: 36px; font-weight: 500; margin: 16px 0 0 0; color: #3f51b5; }
    .avatar {
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      color: white;
    }
    /* COLORES */
    .total-card { border-top-color: #607d8b; }
    .total { background-color: #607d8b; }
    .ready { background-color: #3f51b5; }
    .pending { background-color: #ff9800; }
    .executed { background-color: #4caf50; }
    .failed { background-color: #f44336; }
  `]
})
export class DashboardComponent implements OnInit {
  stats = signal({ total: 0, ready: 0, pending: 0, executed: 0, failed: 0 });
  loading = signal(true);

  constructor(private routeService: RouteService) {}

  ngOnInit(): void {
    this.loadStats();
  }

  loadStats(): void {
    this.loading.set(true);
    this.routeService.getDashboardStats().subscribe({
      next: (res) => {
        if (res.success) {
          this.stats.set(res.data);
        }
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }
}
