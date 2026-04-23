// src/app/shared/components/layout/layout.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatToolbarModule,
    MatButtonModule,
    MatSidenavModule,
    MatIconModule,
    MatListModule,
    MatMenuModule
  ],
  template: `
    <mat-toolbar color="primary" class="header">
      <button mat-icon-button (click)="sidenav.toggle()">
        <mat-icon>menu</mat-icon>
      </button>
      <span>Logistics Routes System</span>
      <span class="spacer"></span>
      <span class="user-name" *ngIf="authService.currentUser()">
        {{ authService.currentUser()?.first_name || authService.currentUser()?.username }}
      </span>
      <button mat-icon-button [matMenuTriggerFor]="menu">
        <mat-icon>account_circle</mat-icon>
      </button>
      <mat-menu #menu="matMenu">
        <button mat-menu-item (click)="logout()">
          <mat-icon>exit_to_app</mat-icon>
          <span>Cerrar sesión</span>
        </button>
      </mat-menu>
    </mat-toolbar>

    <mat-sidenav-container class="sidenav-container">
      <mat-sidenav #sidenav mode="side" opened class="sidenav">
        <mat-nav-list>
          <a mat-list-item routerLink="/dashboard" routerLinkActive="active-link">
            <mat-icon matListItemIcon>dashboard</mat-icon>
            <span matListItemTitle>Dashboard</span>
          </a>
          <a mat-list-item routerLink="/routes" routerLinkActive="active-link">
            <mat-icon matListItemIcon>route</mat-icon>
            <span matListItemTitle>Rutas</span>
          </a>
          <a mat-list-item routerLink="/import" routerLinkActive="active-link">
            <mat-icon matListItemIcon>upload_file</mat-icon>
            <span matListItemTitle>Importar Excel</span>
          </a>
          <a mat-list-item routerLink="/logs" routerLinkActive="active-link">
            <mat-icon matListItemIcon>history</mat-icon>
            <span matListItemTitle>Auditoría de Logs</span>
          </a>
        </mat-nav-list>
      </mat-sidenav>

      <mat-sidenav-content class="content">
        <div class="main-container">
          <router-outlet></router-outlet>
        </div>
      </mat-sidenav-content>
    </mat-sidenav-container>
  `,
  styles: [`
    .sidenav-container {
      height: calc(100vh - 64px);
    }
    .sidenav {
      width: 250px;
      border-right: none;
      background: #fff;
      box-shadow: 2px 0 5px rgba(0,0,0,0.02);
    }
    .header {
      position: sticky;
      top: 0;
      z-index: 1000;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .content {
      background-color: #f5f7fa;
    }
    .main-container {
      padding: 32px;
      min-height: 100%;
      box-sizing: border-box;
    }
    .active-link {
      background: rgba(63, 81, 181, 0.1);
      color: #3f51b5 !important;
      border-left: 4px solid #3f51b5;
    }
    .spacer {
      flex: 1 1 auto;
    }
    .user-name {
      font-size: 14px;
      margin-right: 8px;
    }
  `]
})
export class LayoutComponent {
  constructor(public authService: AuthService) {}

  logout() {
    this.authService.logout();
  }
}
