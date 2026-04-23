import { Component, OnInit, ViewChild, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatCardModule } from '@angular/material/card';
import { SelectionModel } from '@angular/cdk/collections';
import { RouteService } from '../../../core/services/route.service';
import { Route } from '../../../core/models/route.model';
import { RouteDetailDialogComponent } from '../route-detail-dialog/route-detail-dialog.component';
import { debounceTime, distinctUntilChanged } from 'rxjs';

@Component({
  selector: 'app-route-list',
  standalone: true,
  imports: [
    CommonModule, 
    ReactiveFormsModule,
    MatTableModule, 
    MatPaginatorModule, 
    MatSortModule, 
    MatIconModule, 
    MatButtonModule,
    MatChipsModule,
    MatTooltipModule,
    MatProgressBarModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSnackBarModule,
    MatDialogModule,
    MatCheckboxModule,
    MatCardModule
  ],
  template: `
    <div class="header-section">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <h1>Gestión de Rutas</h1>
          <p class="subtitle">Administra, filtra y ejecuta rutas de forma individual o masiva.</p>
        </div>
        <div class="actions">
          <button mat-flat-button color="accent" class="me-2 pulse-animation" 
                  *ngIf="selection.hasValue()" (click)="executeSelectedRoutes()">
            <mat-icon>play_circle</mat-icon> Ejecutar seleccionadas ({{ selection.selected.length }})
          </button>
          
          <button mat-stroked-button color="primary" class="me-2" (click)="resetFilters()">
            <mat-icon>filter_list_off</mat-icon> Limpiar
          </button>
          <button mat-raised-button color="primary" (click)="loadRoutes()">
            <mat-icon>refresh</mat-icon> Actualizar
          </button>
        </div>
      </div>
    </div>

    <!-- Barra de Filtros -->
    <mat-card class="filter-card shadow-card mb-4">
      <form [formGroup]="filterForm" class="filter-form">
        <mat-form-field appearance="outline">
          <mat-label>Origen</mat-label>
          <input matInput formControlName="origin" placeholder="Ej: Bogotá">
          <mat-icon matSuffix>location_on</mat-icon>
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Destino</mat-label>
          <input matInput formControlName="destination" placeholder="Ej: Medellín">
          <mat-icon matSuffix>near_me</mat-icon>
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Estado</mat-label>
          <mat-select formControlName="status">
            <mat-option [value]="''">Todos</mat-option>
            <mat-option value="READY">READY</mat-option>
            <mat-option value="PENDING">PENDING</mat-option>
            <mat-option value="EXECUTED">EXECUTED</mat-option>
            <mat-option value="FAILED">FAILED</mat-option>
          </mat-select>
        </mat-form-field>
        
        <mat-form-field appearance="outline">
          <mat-label>Prioridad</mat-label>
          <input matInput type="number" formControlName="priority" placeholder="Ej: 1">
        </mat-form-field>
      </form>
    </mat-card>

    <mat-progress-bar *ngIf="loading()" mode="indeterminate" class="mb-2"></mat-progress-bar>

    <div class="mat-elevation-z8 shadow-card overflow-hidden">
      <table mat-table [dataSource]="dataSource" matSort>

        <!-- Checkbox Column -->
        <ng-container matColumnDef="select">
          <th mat-header-cell *matHeaderCellDef>
            <mat-checkbox (change)="$event ? masterToggle() : null"
                          [checked]="selection.hasValue() && isAllSelected()"
                          [indeterminate]="selection.hasValue() && !isAllSelected()">
            </mat-checkbox>
          </th>
          <td mat-cell *matCellDef="let row">
            <mat-checkbox (click)="$event.stopPropagation()"
                          (change)="$event ? selection.toggle(row) : null"
                          [checked]="selection.isSelected(row)"
                          [disabled]="row.status !== 'READY'">
            </mat-checkbox>
          </td>
        </ng-container>

        <ng-container matColumnDef="id_route">
          <th mat-header-cell *matHeaderCellDef mat-sort-header> ID Ruta </th>
          <td mat-cell *matCellDef="let row"> <b>#{{row.id_route}}</b> </td>
        </ng-container>

        <ng-container matColumnDef="origin">
          <th mat-header-cell *matHeaderCellDef mat-sort-header> Origen </th>
          <td mat-cell *matCellDef="let row"> {{row.origin}} </td>
        </ng-container>

        <ng-container matColumnDef="destination">
          <th mat-header-cell *matHeaderCellDef mat-sort-header> Destino </th>
          <td mat-cell *matCellDef="let row"> {{row.destination}} </td>
        </ng-container>

        <ng-container matColumnDef="distance_km">
          <th mat-header-cell *matHeaderCellDef mat-sort-header> Distancia </th>
          <td mat-cell *matCellDef="let row"> {{row.distance_km}} km </td>
        </ng-container>

        <ng-container matColumnDef="status">
          <th mat-header-cell *matHeaderCellDef mat-sort-header> Estado </th>
          <td mat-cell *matCellDef="let row">
            <mat-chip-set>
              <mat-chip [class]="'status-chip ' + row.status.toLowerCase()" disabled>
                {{row.status}}
              </mat-chip>
            </mat-chip-set>
          </td>
        </ng-container>

        <ng-container matColumnDef="created_at">
          <th mat-header-cell *matHeaderCellDef mat-sort-header> Fecha </th>
          <td mat-cell *matCellDef="let row"> {{row.created_at | date:'short'}} </td>
        </ng-container>

        <ng-container matColumnDef="actions">
          <th mat-header-cell *matHeaderCellDef> Acciones </th>
          <td mat-cell *matCellDef="let row">
            <button mat-icon-button color="primary" matTooltip="Ver detalles" (click)="viewDetails(row)">
              <mat-icon>visibility</mat-icon>
            </button>
            <button mat-icon-button color="accent" matTooltip="Ejecutar" 
                    [disabled]="row.status !== 'READY' || loading()"
                    (click)="executeSingleRoute(row.id_route)">
              <mat-icon>play_circle</mat-icon>
            </button>
          </td>
        </ng-container>

        <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
        <tr mat-row *matRowDef="let row; columns: displayedColumns;" (click)="row.status === 'READY' && selection.toggle(row)"></tr>
        <tr class="mat-row" *matNoDataRow>
          <td class="mat-cell p-4 text-center" colspan="7">No se encontraron rutas.</td>
        </tr>
      </table>

      <mat-paginator 
        [length]="totalResults()" 
        [pageSize]="pageSize" 
        [pageSizeOptions]="[10, 25, 50]" 
        (page)="onPageChange($event)"
        aria-label="Seleccionar página">
      </mat-paginator>
    </div>
  `,
  styles: [`
    .header-section { margin-bottom: 24px; }
    h1 { margin: 0; font-weight: 500; }
    .subtitle { color: #666; }
    .filter-card { padding: 20px 20px 0 20px; }
    .filter-form {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
    }
    .status-chip { font-weight: 500 !important; }
    .ready { background-color: #e8eaf6; color: #3f51b5; }
    .pending { background-color: #fff3e0; color: #ef6c00; }
    .executed { background-color: #e8f5e9; color: #2e7d32; }
    .failed { background-color: #ffebee; color: #c62828; }
    .mb-2 { margin-bottom: 8px; }
    .mb-4 { margin-bottom: 24px; }
    .me-2 { margin-right: 8px; }
    .d-flex { display: flex; }
    .justify-content-between { justify-content: space-between; }
    .align-items-center { align-items: center; }
    .overflow-hidden { border-radius: 12px; overflow: hidden; }
    
    .pulse-animation {
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(255, 64, 129, 0.4); }
      70% { box-shadow: 0 0 0 10px rgba(255, 64, 129, 0); }
      100% { box-shadow: 0 0 0 0 rgba(255, 64, 129, 0); }
    }
  `]
})
export class RouteListComponent implements OnInit {
  displayedColumns: string[] = ['select', 'id_route', 'origin', 'destination', 'status', 'created_at', 'actions'];
  dataSource = new MatTableDataSource<Route>([]);
  selection = new SelectionModel<Route>(true, []);
  
  loading = signal(false);
  totalResults = signal(0);
  pageSize = 50;
  currentPage = 1;

  filterForm: FormGroup;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private routeService: RouteService,
    private fb: FormBuilder,
    private snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {
    this.filterForm = this.fb.group({
      origin: [''],
      destination: [''],
      status: [''],
      priority: ['']
    });
  }

  ngOnInit(): void {
    this.loadRoutes();

    // Filtro reactivo con debounce para no saturar el backend
    this.filterForm.valueChanges.pipe(
      debounceTime(400),
      distinctUntilChanged()
    ).subscribe(() => {
      this.currentPage = 1;
      this.loadRoutes();
    });
  }

  /** Determina si todos los elementos READY de la página están seleccionados */
  isAllSelected(): boolean {
    const readyOnPage = this.dataSource.data.filter(r => r.status === 'READY');
    const numSelected = this.selection.selected.length;
    const numRows = readyOnPage.length;
    return numSelected === numRows;
  }

  /** Selecciona o deselecciona todas las rutas READY de la página activa */
  masterToggle(): void {
    if (this.isAllSelected()) {
      this.selection.clear();
    } else {
      this.dataSource.data.forEach(row => {
        if (row.status === 'READY') {
          this.selection.select(row);
        }
      });
    }
  }

  loadRoutes(): void {
    this.loading.set(true);
    this.selection.clear();
    const filters = {
      ...this.filterForm.value,
      page: this.currentPage,
      page_size: this.pageSize
    };

    this.routeService.getRoutes(filters).subscribe({
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
    this.loadRoutes();
  }

  resetFilters(): void {
    this.filterForm.reset({ status: '' });
  }

  viewDetails(route: Route): void {
    const dialogRef = this.dialog.open(RouteDetailDialogComponent, {
      width: '600px',
      data: route
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result === 'execute') {
        this.executeSingleRoute(route.id_route);
      }
    });
  }

  executeSingleRoute(id_route: string): void {
    this.executeBulk([id_route], `Ruta #${id_route} enviada a ejecución`);
  }

  executeSelectedRoutes(): void {
    const ids = this.selection.selected.map(r => r.id_route);
    this.executeBulk(ids, `Procesando ejecución masiva de ${ids.length} rutas`);
  }

  private executeBulk(ids: string[], message: string): void {
    this.loading.set(true);
    this.routeService.executeRoutes(ids).subscribe({
      next: () => {
        this.snackBar.open(message, 'Cerrar', { duration: 3000 });
        this.loadRoutes();
      },
      error: () => {
        this.snackBar.open('Error al ejecutar la acción', 'Cerrar', { duration: 3000 });
        this.loading.set(false);
      }
    });
  }
}
