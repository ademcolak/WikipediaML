#!/usr/bin/env python3
"""
visualize_results.py
--------------------
Benchmark sonuçlarını görselleştir.

Özellikler:
- Hız dağılımı
- Tıklama dağılımı
- Başarı oranı (zorluk bazlı)
- Algoritma karşılaştırması

Kullanım:
    python benchmark/visualize_results.py benchmark/results_greedy_*.json
    python benchmark/visualize_results.py benchmark/results_*.json --compare
"""

import argparse
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from typing import List, Dict
import statistics


class ResultsVisualizer:
    """Benchmark sonuçlarını görselleştir."""
    
    def __init__(self):
        self.results_data = []
    
    def load_results(self, result_files: List[str]):
        """Sonuç dosyalarını yükle."""
        print(f"\n📂 {len(result_files)} sonuç dosyası yükleniyor...")
        
        for file in result_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.results_data.append({
                        'file': file,
                        'data': data
                    })
                print(f"✅ {Path(file).name}")
            except Exception as e:
                print(f"❌ {Path(file).name}: {e}")
        
        print(f"\n✅ {len(self.results_data)} dosya yüklendi")
    
    def create_single_dashboard(self, results_data: Dict):
        """Tek bir sonuç için dashboard oluştur."""
        data = results_data['data']
        metadata = data['metadata']
        analysis = data['analysis']
        results = data['results']
        
        # Başarılı test'leri filtrele
        successful = [r for r in results if r['success']]
        
        if not successful:
            print("⚠️  Başarılı test yok, görselleştirme yapılamıyor")
            return None
        
        # 2x2 subplot
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Süre Dağılımı',
                'Tıklama Dağılımı',
                'Zorluk Bazlı Başarı Oranı',
                'Süre vs Tıklama'
            ),
            specs=[
                [{"type": "histogram"}, {"type": "histogram"}],
                [{"type": "bar"}, {"type": "scatter"}]
            ]
        )
        
        # 1. Süre dağılımı
        times = [r['time'] for r in successful]
        fig.add_trace(
            go.Histogram(
                x=times,
                name='Süre',
                marker_color='lightblue',
                nbinsx=20
            ),
            row=1, col=1
        )
        
        # 2. Tıklama dağılımı
        clicks = [r['clicks'] for r in successful]
        fig.add_trace(
            go.Histogram(
                x=clicks,
                name='Tıklama',
                marker_color='lightgreen',
                nbinsx=max(clicks) - min(clicks) + 1
            ),
            row=1, col=2
        )
        
        # 3. Zorluk bazlı başarı oranı
        if 'by_difficulty' in analysis:
            difficulties = []
            success_rates = []
            colors = []
            
            for diff, stats in analysis['by_difficulty'].items():
                difficulties.append(diff.capitalize())
                success_rates.append(stats['success_rate'])
                colors.append({
                    'easy': 'lightgreen',
                    'medium': 'orange',
                    'hard': 'red'
                }.get(diff, 'gray'))
            
            fig.add_trace(
                go.Bar(
                    x=difficulties,
                    y=success_rates,
                    name='Başarı Oranı',
                    marker_color=colors,
                    text=[f"%{sr:.1f}" for sr in success_rates],
                    textposition='outside'
                ),
                row=2, col=1
            )
        
        # 4. Süre vs Tıklama scatter
        fig.add_trace(
            go.Scatter(
                x=clicks,
                y=times,
                mode='markers',
                name='Test',
                marker=dict(
                    size=8,
                    color=times,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(
                        title="Süre (s)",
                        x=1.15
                    )
                ),
                text=[f"{r['start']} → {r['target']}" for r in successful],
                hovertemplate='<b>%{text}</b><br>Tıklama: %{x}<br>Süre: %{y:.2f}s<extra></extra>'
            ),
            row=2, col=2
        )
        
        # Layout
        algorithm = metadata['algorithm']
        title = f"Benchmark Sonuçları - {algorithm.upper()}"
        if algorithm == 'beam':
            title += f" (width={metadata['beam_width']})"
        
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            ),
            showlegend=False,
            height=800,
            paper_bgcolor='white',
            plot_bgcolor='rgba(240, 240, 240, 0.5)'
        )
        
        # Axis labels
        fig.update_xaxes(title_text="Süre (saniye)", row=1, col=1)
        fig.update_yaxes(title_text="Test Sayısı", row=1, col=1)
        
        fig.update_xaxes(title_text="Tıklama Sayısı", row=1, col=2)
        fig.update_yaxes(title_text="Test Sayısı", row=1, col=2)
        
        fig.update_xaxes(title_text="Zorluk", row=2, col=1)
        fig.update_yaxes(title_text="Başarı Oranı (%)", row=2, col=1)
        
        fig.update_xaxes(title_text="Tıklama Sayısı", row=2, col=2)
        fig.update_yaxes(title_text="Süre (saniye)", row=2, col=2)
        
        return fig
    
    def create_comparison_dashboard(self):
        """Birden fazla sonucu karşılaştır."""
        if len(self.results_data) < 2:
            print("⚠️  Karşılaştırma için en az 2 sonuç dosyası gerekli")
            return None
        
        # 2x2 subplot
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Ortalama Süre Karşılaştırması',
                'Ortalama Tıklama Karşılaştırması',
                'Başarı Oranı Karşılaştırması',
                'Süre Dağılımı (Box Plot)'
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "box"}]
            ]
        )
        
        algorithms = []
        avg_times = []
        avg_clicks = []
        success_rates = []
        all_times = []
        
        for result in self.results_data:
            data = result['data']
            metadata = data['metadata']
            analysis = data['analysis']
            
            algo_name = metadata['algorithm']
            if algo_name == 'beam':
                algo_name += f" (w={metadata['beam_width']})"
            
            algorithms.append(algo_name)
            avg_times.append(analysis.get('avg_time', 0))
            avg_clicks.append(analysis.get('avg_clicks', 0))
            success_rates.append(analysis.get('success_rate', 0))
            
            # Tüm süreleri topla
            successful = [r for r in data['results'] if r['success']]
            all_times.append([r['time'] for r in successful])
        
        # 1. Ortalama süre
        fig.add_trace(
            go.Bar(
                x=algorithms,
                y=avg_times,
                name='Ort. Süre',
                marker_color='lightblue',
                text=[f"{t:.2f}s" for t in avg_times],
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # 2. Ortalama tıklama
        fig.add_trace(
            go.Bar(
                x=algorithms,
                y=avg_clicks,
                name='Ort. Tıklama',
                marker_color='lightgreen',
                text=[f"{c:.2f}" for c in avg_clicks],
                textposition='outside'
            ),
            row=1, col=2
        )
        
        # 3. Başarı oranı
        fig.add_trace(
            go.Bar(
                x=algorithms,
                y=success_rates,
                name='Başarı Oranı',
                marker_color='orange',
                text=[f"%{sr:.1f}" for sr in success_rates],
                textposition='outside'
            ),
            row=2, col=1
        )
        
        # 4. Süre dağılımı (box plot)
        for algo, times in zip(algorithms, all_times):
            fig.add_trace(
                go.Box(
                    y=times,
                    name=algo,
                    boxmean='sd'
                ),
                row=2, col=2
            )
        
        # Layout
        fig.update_layout(
            title=dict(
                text="Algoritma Karşılaştırması",
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            ),
            showlegend=False,
            height=800,
            paper_bgcolor='white',
            plot_bgcolor='rgba(240, 240, 240, 0.5)'
        )
        
        # Axis labels
        fig.update_yaxes(title_text="Süre (saniye)", row=1, col=1)
        fig.update_yaxes(title_text="Tıklama Sayısı", row=1, col=2)
        fig.update_yaxes(title_text="Başarı Oranı (%)", row=2, col=1)
        fig.update_yaxes(title_text="Süre (saniye)", row=2, col=2)
        
        return fig
    
    def save_dashboard(self, fig, output_file: str):
        """Dashboard'u HTML olarak kaydet."""
        if fig is None:
            return
        
        print(f"\n💾 Dashboard kaydediliyor: {output_file}")
        fig.write_html(output_file)
        print(f"✅ Dashboard kaydedildi")
        print(f"\n🌐 Görüntülemek için:")
        print(f"   open {output_file}")


def main():
    """Ana fonksiyon."""
    parser = argparse.ArgumentParser(description='Benchmark Sonuçlarını Görselleştir')
    parser.add_argument('files', nargs='+', help='Sonuç dosyaları (JSON)')
    parser.add_argument('--compare', action='store_true',
                       help='Birden fazla sonucu karşılaştır')
    parser.add_argument('--output', type=str,
                       help='Çıktı dosyası (default: benchmark/dashboard.html)')
    
    args = parser.parse_args()
    
    # Output file
    if not args.output:
        if args.compare:
            args.output = 'benchmark/dashboard_comparison.html'
        else:
            args.output = 'benchmark/dashboard.html'
    
    print("="*70)
    print("📊 BENCHMARK GÖRSELLEŞTIRME")
    print("="*70)
    
    # Visualizer oluştur
    visualizer = ResultsVisualizer()
    
    # Sonuçları yükle
    visualizer.load_results(args.files)
    
    # Dashboard oluştur
    if args.compare and len(visualizer.results_data) > 1:
        print("\n🔄 Karşılaştırma dashboard'u oluşturuluyor...")
        fig = visualizer.create_comparison_dashboard()
    else:
        print("\n📊 Dashboard oluşturuluyor...")
        fig = visualizer.create_single_dashboard(visualizer.results_data[0])
    
    # Kaydet
    visualizer.save_dashboard(fig, args.output)
    
    print("\n✅ GÖRSELLEŞTİRME TAMAMLANDI")


if __name__ == "__main__":
    main()