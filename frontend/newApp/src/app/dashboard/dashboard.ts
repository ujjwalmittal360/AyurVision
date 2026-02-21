import { Component, ChangeDetectorRef } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';

import { CommonModule } from '@angular/common';
@Component({
  selector: 'app-dashboard',
  imports: [MatCardModule, MatIconModule, MatButtonModule, MatChipsModule, CommonModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard {
  selectedFile: File | null = null;
  imagePreview: string | ArrayBuffer | null = null;
  result: any = null;
  loading = false;

  constructor(private http: HttpClient, private cdr: ChangeDetectorRef) { }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (!file) return;

    this.selectedFile = file;

    const reader = new FileReader();
    reader.onload = () => {
      this.imagePreview = reader.result;
      this.cdr.detectChanges();
    };
    reader.readAsDataURL(file);
  }

  removeImage() {
    this.selectedFile = null;
    this.imagePreview = null;
    this.result = null;
  }

  uploadFile() {
    if (!this.selectedFile) return;

    this.loading = true;

    const formData = new FormData();
    formData.append('file', this.selectedFile);

    const token = sessionStorage.getItem('token');
    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });

    this.http.post('http://localhost:8000/predict', formData, { headers }).subscribe({
      next: (res: any) => {

        this.result = {
          common_name: res.common_name || res.plant_name,
          scientific_name: res.scientific_name,
          confidence: res.confidence,
          description: res.description,
          properties: res.properties,
          medicinal_uses: res.medicinal_uses,
          parts_used: res.parts_used,
          preparation: res.preparation,
          market_value: res.market_value,
          sowing: res.sowing,
          harvest: res.harvest,
          toxicity: res.toxicity
        };
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.loading = false;
        this.cdr.detectChanges();
        alert(err.error?.detail || 'No plant matched');
      },
    });
  }
}
