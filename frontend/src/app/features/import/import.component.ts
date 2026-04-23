// src/app/features/import/import.component.ts
import { Component, signal, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { RouteService } from '../../core/services/route.service';

@Component({
  selector: 'app-import',
  standalone: true,
  imports: [
    CommonModule, 
    MatCardModule, 
    MatButtonModule, 
    MatIconModule, 
    MatProgressBarModule,
    MatTableModule,
    MatPaginatorModule,
    MatSnackBarModule
  ],
  template: `
    <div class="header-section">
      <h1>Importación de Datos</h1>
      <p class="subtitle">Carga masiva de rutas mediante archivos Excel (.xlsx).</p>
    </div>

    <div class="import-container">
      <mat-card class="upload-card shadow-card fixed-height">
        <mat-card-header>
          <mat-card-title>Seleccionar Archivo</mat-card-title>
          <mat-card-subtitle>Asegúrese que el archivo siga el formato establecido.</mat-card-subtitle>
        </mat-card-header>
        
        <mat-card-content class="drop-zone">
          <input type="file" #fileInput (change)="onFileSelected($event)" accept=".xlsx" style="display: none">
          
          <div class="upload-info" *ngIf="!selectedFile()">
            <mat-icon class="upload-icon">cloud_upload</mat-icon>
            <p>Haga clic para seleccionar su archivo Excel</p>
            <button mat-stroked-button color="primary" (click)="fileInput.click()">
              Buscar Archivo
            </button>
          </div>

          <div class="selected-file" *ngIf="selectedFile()">
            <mat-icon color="primary">description</mat-icon>
            <span class="file-name text-truncate">{{ selectedFile()?.name }}</span>
            <button mat-icon-button color="warn" (click)="clearSelection()">
              <mat-icon>close</mat-icon>
            </button>
          </div>
        </mat-card-content>

        <mat-progress-bar *ngIf="loading()" mode="indeterminate"></mat-progress-bar>

        <mat-card-actions align="end">
          <button mat-raised-button color="primary" 
                   [disabled]="!selectedFile() || loading()" 
                   (click)="uploadFile()">
            <mat-icon>upload</mat-icon> Procesar Importación
          </button>
        </mat-card-actions>
      </mat-card>

      <!-- Panel de Resultados -->
      <mat-card class="results-card shadow-card fixed-height" *ngIf="results()">
        <mat-card-header>
          <mat-card-title>Resumen de Resultados</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="stats-summary">
            <div class="stat-item success">
              <span class="label">Importadas</span>
              <span class="value">{{ results()?.summary?.imported || 0 }}</span>
            </div>
            <div class="stat-item warning">
              <span class="label">Duplicadas</span>
              <span class="value">{{ results()?.summary?.duplicates || 0 }}</span>
            </div>
            <div class="stat-item error">
              <span class="label">Errores</span>
              <span class="value">{{ results()?.summary?.errors || 0 }}</span>
            </div>
          </div>

          <div class="table-container" *ngIf="dataSource.data.length > 0">
            <h3>Detalle de Errores:</h3>
            <div class="mat-elevation-z2 table-wrapper">
              <table mat-table [dataSource]="dataSource">
                <ng-container matColumnDef="row">
                  <th mat-header-cell *matHeaderCellDef>Fila</th>
                  <td mat-cell *matCellDef="let element"> {{element.row}} </td>
                </ng-container>

                <ng-container matColumnDef="id_route">
                  <th mat-header-cell *matHeaderCellDef>Ruta (ID)</th>
                  <td mat-cell *matCellDef="let element" class="id-cell"> {{element.id_route}} </td>
                </ng-container>

                <ng-container matColumnDef="reason">
                  <th mat-header-cell *matHeaderCellDef>Razón del Fallo</th>
                  <td mat-cell *matCellDef="let element"> {{element.reason}} </td>
                </ng-container>

                <tr mat-header-row *matHeaderRowDef="displayedColumns; sticky: true"></tr>
                <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
              </table>
              <mat-paginator [pageSizeOptions]="[5, 10, 20]" showFirstLastButtons aria-label="Seleccionar página"></mat-paginator>
            </div>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .import-container {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
      gap: 24px;
      align-items: stretch;
    }
    .header-section { margin-bottom: 32px; }
    h1 { margin: 0; font-weight: 500; }
    .subtitle { color: #666; }
    
    .fixed-height { min-height: 500px; display: flex; flex-direction: column; }
    .upload-card mat-card-content { flex-grow: 1; display: flex; align-items: center; justify-content: center; }

    .drop-zone {
      border: 2px dashed #e0e0e0;
      border-radius: 8px;
      padding: 40px;
      text-align: center;
      background: #fafafa;
      width: 100%;
      box-sizing: border-box;
    }
    .upload-icon { font-size: 48px; width: 48px; height: 48px; color: #bdbdbd; margin-bottom: 16px; }
    .selected-file {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      padding: 12px;
      background: #e8eaf6;
      border-radius: 4px;
      width: 100%;
    }
    .text-truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
    .file-name { font-weight: 500; }

    .stats-summary {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
    }
    .stat-item {
      flex: 1;
      padding: 12px;
      border-radius: 8px;
      text-align: center;
      display: flex;
      flex-direction: column;
    }
    .stat-item .label { font-size: 11px; text-transform: uppercase; margin-bottom: 2px; }
    .stat-item .value { font-size: 20px; font-weight: bold; }
    
    .success { background: #e8f5e9; color: #2e7d32; }
    .warning { background: #fff3e0; color: #ef6c00; }
    .error { background: #ffebee; color: #c62828; }

    .table-container { flex-grow: 1; display: flex; flex-direction: column; }
    .table-wrapper { 
      flex-grow: 1; 
      max-height: 300px; 
      overflow: auto; 
      border: 1px solid #eee;
      border-radius: 4px;
    }
    h3 { font-size: 14px; color: #333; margin-bottom: 8px; font-weight: 500; }
    table { width: 100%; }
    .id-cell { font-family: monospace; font-weight: bold; color: #3f51b5; }
    td.mat-cell { font-size: 12px; padding: 0 8px; }
    th.mat-header-cell { background: #f5f5f5; font-size: 11px; font-weight: bold; }
  `]
})
export class ImportComponent {
  selectedFile = signal<File | null>(null);
  loading = signal(false);
  results = signal<any>(null);

  displayedColumns: string[] = ['row', 'id_route', 'reason'];
  dataSource = new MatTableDataSource<any>([]);

  @ViewChild(MatPaginator) set paginator(paginator: MatPaginator) {
    if (paginator) {
      this.dataSource.paginator = paginator;
    }
  }

  constructor(
    private routeService: RouteService,
    private snackBar: MatSnackBar
  ) {}

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile.set(file);
      this.results.set(null);
      this.dataSource.data = [];
    }
  }

  clearSelection(): void {
    this.selectedFile.set(null);
    this.results.set(null);
    this.dataSource.data = [];
  }

  uploadFile(): void {
    const file = this.selectedFile();
    if (!file) return;

    this.loading.set(true);
    this.routeService.importRoutes(file).subscribe({
      next: (res) => {
        this.results.set(res.data);
        this.dataSource.data = res.data.errors || [];
        this.loading.set(false);
        this.snackBar.open('Proceso de importación finalizado', 'Cerrar', { duration: 4000 });
        if (res.data.summary.imported > 0) {
          this.selectedFile.set(null);
        }
      },
      error: (err) => {
        this.loading.set(false);
        const errorMsg = err.error?.error?.detail || 'Error crítico al procesar el archivo';
        const formattedMsg = typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : errorMsg;
        this.snackBar.open(formattedMsg, 'Cerrar', { duration: 6000 });
      }
    });
  }
}
