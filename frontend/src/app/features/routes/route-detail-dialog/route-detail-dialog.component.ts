// src/app/features/routes/route-detail-dialog/route-detail-dialog.component.ts
import { Component, Inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatListModule } from '@angular/material/list';
import { MatChipsModule } from '@angular/material/chips';
import { RouteService } from '../../../core/services/route.service';
import { Route } from '../../../core/models/route.model';

@Component({
  selector: 'app-route-detail-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatDividerModule,
    MatListModule,
    MatChipsModule
  ],
  template: `
    <h2 mat-dialog-title>Detalle de Ruta #{{ data.id_route }}</h2>
    
    <mat-dialog-content class="mat-typography">
      <div class="detail-grid">
        <div class="info-item">
          <label>Estado Actual</label>
          <mat-chip-set>
            <mat-chip [class]="'status-chip ' + data.status.toLowerCase()" disabled>{{ data.status }}</mat-chip>
          </mat-chip-set>
        </div>
        <div class="info-item">
          <label>Prioridad</label>
          <p>{{ data.priority }}</p>
        </div>
        <div class="info-item">
          <label>Origen</label>
          <p>{{ data.origin }}</p>
        </div>
        <div class="info-item">
          <label>Destino</label>
          <p>{{ data.destination }}</p>
        </div>
        <div class="info-item">
          <label>Distancia</label>
          <p>{{ data.distance_km }} km</p>
        </div>
        <div class="info-item">
          <label>Ventana Horaria</label>
          <p>{{ data.time_window_start | date:'short' }} - {{ data.time_window_end | date:'shortTime' }}</p>
        </div>
      </div>

      <mat-divider class="my-4"></mat-divider>

      <h3>Datos Adicionales (Payload)</h3>
      <pre class="payload-box">{{ data.payload | json }}</pre>

      <mat-divider class="my-4"></mat-divider>

      <h3>Historial de Ejecución (Logs)</h3>
      <div *ngIf="loading(); else logsList" class="text-center p-3">Cargando logs...</div>
      
      <ng-template #logsList>
        <mat-list *ngIf="logs().length > 0; else noLogs">
          <mat-list-item *ngFor="let log of logs()">
            <mat-icon matListItemIcon [color]="log.result === 'SUCCESS' ? 'primary' : 'warn'">
              {{ log.result === 'SUCCESS' ? 'check_circle' : 'error' }}
            </mat-icon>
            <div matListItemTitle>{{ log.result }} - {{ log.execution_time | date:'medium' }}</div>
            <div matListItemLine>{{ log.message }}</div>
          </mat-list-item>
        </mat-list>
        <ng-template #noLogs>
          <p class="text-muted">No hay registros de ejecución para esta ruta.</p>
        </ng-template>
      </ng-template>
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cerrar</button>
      <button mat-raised-button color="accent" *ngIf="data.status === 'READY'" (click)="execute()">
        <mat-icon>play_arrow</mat-icon> Ejecutar Ahora
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    .detail-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 16px;
    }
    .info-item label {
      font-size: 12px;
      color: #777;
      display: block;
      margin-bottom: 4px;
      text-transform: uppercase;
    }
    .info-item p { margin: 0; font-weight: 500; font-size: 16px; }
    .my-4 { margin: 24px 0; }
    h3 { font-size: 14px; color: #3f51b5; text-transform: uppercase; margin-bottom: 12px; }
    .payload-box {
      background: #263238;
      color: #80cbc4;
      padding: 16px;
      border-radius: 8px;
      font-size: 12px;
      overflow-x: auto;
      max-height: 200px;
    }
    .status-chip { font-weight: 500 !important; }
    .ready { background-color: #e8eaf6; color: #3f51b5; }
    .pending { background-color: #fff3e0; color: #ef6c00; }
    .executed { background-color: #e8f5e9; color: #2e7d32; }
    .failed { background-color: #ffebee; color: #c62828; }
  `]
})
export class RouteDetailDialogComponent implements OnInit {
  logs = signal<any[]>([]);
  loading = signal(true);

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: Route,
    private dialogRef: MatDialogRef<RouteDetailDialogComponent>,
    private routeService: RouteService
  ) {}

  ngOnInit(): void {
    this.loadLogs();
  }

  loadLogs(): void {
    this.routeService.getRouteLogs(this.data.id_route).subscribe({
      next: (res) => {
        this.logs.set(res.data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  execute(): void {
    this.dialogRef.close('execute');
  }
}
