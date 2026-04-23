// src/app/core/services/route.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { 
  ApiResponse, 
  PaginatedResponse, 
  Route, 
  ExecutionLog 
} from '../models/route.model';

@Injectable({
  providedIn: 'root'
})
export class RouteService {
  private readonly apiUrl = `${environment.apiUrl}/routes/`;

  constructor(private http: HttpClient) {}

  getRoutes(filters: any = {}): Observable<ApiResponse<PaginatedResponse<Route>>> {
    let params = new HttpParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        params = params.set(key, filters[key]);
      }
    });
    return this.http.get<ApiResponse<PaginatedResponse<Route>>>(this.apiUrl, { params });
  }

  getRouteDetail(idRoute: string): Observable<ApiResponse<Route>> {
    return this.http.get<ApiResponse<Route>>(`${this.apiUrl}${idRoute}/`);
  }

  getRouteLogs(idRoute: string): Observable<ApiResponse<ExecutionLog[]>> {
    return this.http.get<ApiResponse<ExecutionLog[]>>(`${this.apiUrl}${idRoute}/logs/`);
  }

  getDashboardStats(): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(`${environment.apiUrl}/dashboard/stats/`);
  }

  importRoutes(file: File): Observable<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<ApiResponse<any>>(`${this.apiUrl}import/`, formData);
  }

  executeRoutes(routeIds: string[]): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(`${this.apiUrl}execute/`, { route_ids: routeIds });
  }

  getGlobalLogs(page: number = 1, pageSize: number = 50): Observable<ApiResponse<PaginatedResponse<ExecutionLog>>> {
    const url = `${environment.apiUrl}/logs/`;
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    return this.http.get<ApiResponse<PaginatedResponse<ExecutionLog>>>(url, { params });
  }
}
