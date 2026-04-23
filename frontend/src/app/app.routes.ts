import { Routes } from '@angular/router';
import { LayoutComponent } from './shared/components/layout/layout.component';

export const routes: Routes = [
  {
    path: '',
    component: LayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { 
        path: 'dashboard', 
        loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent) 
      },
      { 
        path: 'routes', 
        loadComponent: () => import('./features/routes/route-list/route-list.component').then(m => m.RouteListComponent) 
      },
      { 
        path: 'import', 
        loadComponent: () => import('./features/import/import.component').then(m => m.ImportComponent) 
      },
      { 
        path: 'logs', 
        loadComponent: () => import('./features/logs/log-list/log-list.component').then(m => m.LogListComponent) 
      }
    ]
  },
  { path: '**', redirectTo: 'dashboard' }
];
