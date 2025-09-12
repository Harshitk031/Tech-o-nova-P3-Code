#!/usr/bin/env python3
"""
Database Performance Analysis Web Application
Flask-based dashboard for database performance monitoring and alerting.
"""

from flask import Flask, render_template, jsonify, request
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.analysis.enhanced_analysis import EnhancedAnalysisPipeline
from src.analysis.regression_analysis import PerformanceRegressionAnalyzer
from src.analysis.configuration_analysis import ConfigurationAnalyzer
from src.analysis.schema_analysis import SchemaAnalyzer
from src.config.database_config import get_database_config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'db-performance-analysis-2024'

# Initialize analysis components
enhanced_pipeline = EnhancedAnalysisPipeline()
regression_analyzer = PerformanceRegressionAnalyzer()
config_analyzer = ConfigurationAnalyzer()
schema_analyzer = SchemaAnalyzer()

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Performance dashboard."""
    return render_template('dashboard.html')

@app.route('/alerts')
def alerts():
    """Alerts and notifications page."""
    return render_template('alerts.html')

@app.route('/configuration')
def configuration():
    """Configuration analysis page."""
    return render_template('configuration.html')

@app.route('/schema')
def schema():
    """Schema analysis page."""
    return render_template('schema.html')

# API Endpoints

@app.route('/api/hotspots')
def api_hotspots():
    """Get performance hotspots from historical data."""
    try:
        # Get slowest queries from historical data
        regressions = regression_analyzer.find_all_regressions(days=7, threshold=0.3)
        
        # Format for frontend
        hotspots = []
        for reg in regressions[:20]:  # Top 20
            hotspots.append({
                'query_id': reg.get('query_id'),
                'query_text': reg.get('query_text', '')[:100] + '...',
                'database_name': reg.get('database_name'),
                'regression_percentage': reg.get('regression_percentage', 0),
                'severity': reg.get('severity', 'UNKNOWN'),
                'confidence': reg.get('confidence', 0),
                'avg_exec_time_ms': reg.get('recent_performance', {}).get('exec_time_ms', 0),
                'calls': reg.get('recent_performance', {}).get('calls', 0)
            })
        
        return jsonify({
            'success': True,
            'data': hotspots,
            'count': len(hotspots),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500

@app.route('/api/performance-summary')
def api_performance_summary():
    """Get overall performance summary."""
    try:
        summary = regression_analyzer.get_performance_summary(days=7)
        
        return jsonify({
            'success': True,
            'data': summary,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {}
        }), 500

@app.route('/api/regressions')
def api_regressions():
    """Get performance regressions."""
    try:
        days = request.args.get('days', 7, type=int)
        threshold = request.args.get('threshold', 0.5, type=float)
        
        regressions = regression_analyzer.find_all_regressions(days=days, threshold=threshold)
        
        return jsonify({
            'success': True,
            'data': regressions,
            'count': len(regressions),
            'parameters': {
                'days': days,
                'threshold': threshold
            },
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500

@app.route('/api/configuration')
def api_configuration():
    """Get configuration analysis."""
    try:
        database = request.args.get('database', 'both')
        
        results = {}
        if database in ['postgresql', 'both']:
            results['postgresql'] = config_analyzer.analyze_postgresql_configuration()
        
        if database in ['mysql', 'both']:
            results['mysql'] = config_analyzer.analyze_mysql_configuration()
        
        return jsonify({
            'success': True,
            'data': results,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {}
        }), 500

@app.route('/api/schema')
def api_schema():
    """Get schema analysis."""
    try:
        database = request.args.get('database', 'both')
        
        results = {}
        if database in ['postgresql', 'both']:
            results['postgresql'] = schema_analyzer.analyze_postgresql_schema()
        
        if database in ['mysql', 'both']:
            results['mysql'] = schema_analyzer.analyze_mysql_schema()
        
        return jsonify({
            'success': True,
            'data': results,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {}
        }), 500

@app.route('/api/health-check')
def api_health_check():
    """Perform comprehensive health check."""
    try:
        database = request.args.get('database', 'both')
        
        health_analysis = enhanced_pipeline.analyze_database_health(database)
        
        return jsonify({
            'success': True,
            'data': health_analysis,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {}
        }), 500

@app.route('/api/query-analysis', methods=['POST'])
def api_query_analysis():
    """Analyze a specific query."""
    try:
        data = request.get_json()
        query = data.get('query')
        database = data.get('database', 'postgresql')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        analysis = enhanced_pipeline.analyze_query_with_regression(query, database)
        
        return jsonify({
            'success': True,
            'data': analysis,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {}
        }), 500

@app.route('/api/alerts')
def api_alerts():
    """Get current alerts and notifications."""
    try:
        # Get regressions as alerts
        regressions = regression_analyzer.find_all_regressions(days=1, threshold=0.5)
        
        alerts = []
        for reg in regressions:
            if reg.get('severity') in ['CRITICAL', 'HIGH']:
                alerts.append({
                    'type': 'performance_regression',
                    'severity': reg.get('severity'),
                    'message': f"Query {reg.get('query_id')} has {reg.get('regression_percentage', 0):.1f}% performance regression",
                    'query_id': reg.get('query_id'),
                    'database': reg.get('database_name'),
                    'timestamp': datetime.now().isoformat()
                })
        
        # Get configuration issues as alerts
        try:
            config_issues = config_analyzer.analyze_postgresql_configuration()
            if 'recommendations' in config_issues:
                for rec in config_issues['recommendations']:
                    if rec.get('severity') in ['CRITICAL', 'HIGH']:
                        alerts.append({
                            'type': 'configuration_issue',
                            'severity': rec.get('severity'),
                            'message': f"Configuration issue: {rec.get('issue')}",
                            'setting': rec.get('setting'),
                            'database': 'postgresql',
                            'timestamp': datetime.now().isoformat()
                        })
        except:
            pass  # Ignore config analysis errors
        
        return jsonify({
            'success': True,
            'data': alerts,
            'count': len(alerts),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("Starting Database Performance Analysis Web Application...")
    print("Dashboard: http://localhost:5000/dashboard")
    print("API Documentation: http://localhost:5000/api/hotspots")
    app.run(debug=True, host='0.0.0.0', port=5000)
