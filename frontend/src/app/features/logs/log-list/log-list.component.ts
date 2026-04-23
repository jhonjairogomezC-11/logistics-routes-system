import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { RouteService } from '../../../core/services/route.service';
import { ExecutionLog } from '../../../core/models/route.model';

@Component({
  selector: 'app-log-list',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatPaginatorModule,
    MatIconModule,
    MatChipsModule,
    MatCardModule,
    MatProgressBarModule,
    MatButtonModule
  ],
  template: `
    <div class="header-section">
      <h1>Auditoría Global de Logs</h1>
      <p class="subtitle">Historial de todas las operaciones, incluyendo registros rechazados durante la carga.</p>
    </div>

    <mat-progress-bar *ngIf="loading()" mode="indeterminate" class="mb-3"></mat-progress-bar>

    <div class="mat-elevation-z8 shadow-card overflow-hidden">
      <table mat-table [dataSource]="dataSource">

        <ng-container matColumnDef="id">
          <th mat-header-cell *matHeaderCellDef> ID Log </th>
          <td mat-cell *matCellDef="let row"> #{{row.id}} </td>
        </ng-container>

        <ng-container matColumnDef="route">
          <th mat-header-cell *matHeaderCellDef> Ruta Ref. </th>
          <td mat-cell *matCellDef="let row"> 
            <!-- Si row.route tiene un valor (ID de la ruta) -->
            <span *ngIf="row.route !== null && row.route !== undefined" class="route-badge">#{{row.route}}</span>
            <!-- Si es nulo, significa que no pudo crearse la ruta -->
            <span *ngIf="row.route === null || row.route === undefined" class="error-badge">ERROR CARGA</span>
          </td>
        </ng-container>

        <ng-container matColumnDef="time">
          <th mat-header-cell *matHeaderCellDef> Fecha/Hora </th>
          <td mat-cell *matCellDef="let row"> {{row.execution_time | date:'medium'}} </td>
        </ng-container>

        <ng-container matColumnDef="result">
          <th mat-header-cell *matHeaderCellDef> Resultado </th>
          <td mat-cell *matCellDef="let row">
            <mat-chip-set>
              <mat-chip [class]="row.result === 'SUCCESS' ? 'chip-success' : 'chip-error'" disabled>
                {{row.result}}
              </mat-chip>
            </mat-chip-set>
          </td>
        </ng-container>

        <ng-container matColumnDef="message">
          <th mat-header-cell *matHeaderCellDef> Mensaje Detallado </th>
          <td mat-cell *matCellDef="let row"> {{row.message}} </td>
        </ng-container>

        <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
        <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>

        <tr class="mat-row" *matNoDataRow>
          <td class="mat-cell p-4 text-center" colspan="5">No hay registros disponibles.</td>
        </tr>
      </table>

      <mat-paginator 
        [length]="totalResults()" 
        [pageSize]="pageSize" 
        [pageSizeOptions]="[10, 25, 50, 100]" 
        (page)="onPageChange($event)"
        aria-label="Seleccionar página">
      </mat-paginator>
    </div>
  `,
  styles: [`
    .header-section { margin-bottom: 24px; }
    h1 { margin: 0; font-weight: 500; }
    .subtitle { color: #666; }
    /* Estilos mejorados para los badges */
    .route-badge { background: #e3f2fd; color: #1565c0; padding: 4px 8px; border-radius: 4px; font-weight: 500; font-family: monospace; }
    .error-badge { background: #fee2e2; color: #dc2626; padding: 4px 8px; border-radius: 4px; font-weight: 500; font-size: 11px; }
    .chip-success { background-color: #e8f5e9 !important; color: #2e7d32 !important; }
    .chip-error { background-color: #ffebee !important; color: #c62828 !important; }
    .mb-3 { margin-bottom: 16px; }
    .shadow-card { border-radius: 12px; overflow: hidden; background: white; }
  `]
})
export class LogListComponent implements OnInit {
  displayedColumns: string[] = ['id', 'route', 'time', 'result', 'message'];
  dataSource = new MatTableDataSource<ExecutionLog>([]);
  loading = signal(false);
  totalResults = signal(0);
  pageSize = 25;
  currentPage = 1;

  constructor(private routeService: RouteService) {}

  ngOnInit(): void {
    this.loadLogs();
  }

  loadLogs(): void {
    this.loading.set(true);
    this.routeService.getGlobalLogs(this.currentPage, this.pageSize).subscribe({
      next: (res) => {
        this.dataSource.data = res.data.results;
        this.totalResults.set(res.data.count);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  onPageChange(event: PageEvent): void {
    this.pageSize = event.pageSize;
    this.currentPage = event.pageIndex + 1;
    this.loadLogs();
  }
}
