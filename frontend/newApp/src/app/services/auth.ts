import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root',
})
export class Auth {
  private apiUrl = 'http://localhost:8000';
  constructor(private http: HttpClient) { }

  login(email: string, password: string) {
    return this.http
      .post<any>(`${this.apiUrl}/login`, {
        email,
        password,
      })
      .pipe(
        tap((response) => {
          sessionStorage.setItem('token', response.access_token);
          sessionStorage.setItem('user', JSON.stringify(response.user));
        }),
      );
  }

  register(name: string, email: string, password: string) {
    return this.http.post(`${this.apiUrl}/register`, {
      name,
      email,
      password,
    });
  }

  logout() {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
  }

  isLoggedIn(): boolean {
    return !!sessionStorage.getItem('token');
  }
}
