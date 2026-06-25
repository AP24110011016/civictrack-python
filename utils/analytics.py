"""
Analytics Engine
Uses Pandas and Matplotlib to analyze complaint data
and generate insights and charts
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime, timedelta
import os
import io
import base64


def complaints_to_dataframe(complaints):
    """Convert MongoDB complaints list to Pandas DataFrame"""
    if not complaints:
        return pd.DataFrame()

    data = []
    for c in complaints:
        data.append({
            'id':            str(c.get('_id', '')),
            'tracking_id':   c.get('trackingId', ''),
            'title':         c.get('title', ''),
            'issue_type':    c.get('issueType', 'other'),
            'priority':      c.get('priority', 'medium'),
            'status':        c.get('status', 'submitted'),
            'department':    c.get('department', ''),
            'ward':          c.get('location', {}).get('ward', 'Unknown'),
            'upvote_count':  c.get('upvoteCount', 0),
            'urgency_score': c.get('urgencyScore', 0),
            'resolution_hours': c.get('resolutionTimeHours', None),
            'created_at':    pd.to_datetime(c.get('createdAt', datetime.now())),
            'resolved_at':   pd.to_datetime(c.get('resolvedAt')) if c.get('resolvedAt') else None,
            'is_resolved':   c.get('status') == 'resolved',
        })

    df = pd.DataFrame(data)
    if not df.empty:
        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
        df['date']       = df['created_at'].dt.date
    return df


def get_overview_stats(df):
    """Calculate overview statistics using Pandas"""
    if df.empty:
        return {
            'total': 0, 'submitted': 0, 'in_progress': 0,
            'resolved': 0, 'rejected': 0, 'resolution_rate': 0,
            'avg_resolution_hours': 0,
        }

    total    = len(df)
    resolved = len(df[df['status'] == 'resolved'])
    in_prog  = len(df[df['status'].isin(['acknowledged', 'assigned', 'in_progress'])])
    submitted= len(df[df['status'] == 'submitted'])
    rejected = len(df[df['status'] == 'rejected'])

    # Average resolution time using Pandas mean
    res_times = df[df['resolution_hours'].notna()]['resolution_hours']
    avg_res   = round(float(res_times.mean()), 1) if not res_times.empty else 0

    return {
        'total':                total,
        'submitted':            submitted,
        'in_progress':          in_prog,
        'resolved':             resolved,
        'rejected':             rejected,
        'resolution_rate':      round((resolved / total * 100), 1) if total > 0 else 0,
        'avg_resolution_hours': avg_res,
    }


def get_by_type(df):
    """Group complaints by issue type using Pandas"""
    if df.empty:
        return []
    counts = df.groupby('issue_type').size().reset_index(name='count')
    counts = counts.sort_values('count', ascending=False)
    return counts.to_dict('records')


def get_by_priority(df):
    """Group complaints by priority using Pandas"""
    if df.empty:
        return []
    counts = df.groupby('priority').size().reset_index(name='count')
    return counts.to_dict('records')


def get_by_ward(df):
    """Group complaints by ward using Pandas"""
    if df.empty:
        return []
    counts = df.groupby('ward').size().reset_index(name='count')
    counts = counts.sort_values('count', ascending=False).head(10)
    return counts.to_dict('records')


def get_by_status(df):
    """Group complaints by status using Pandas"""
    if df.empty:
        return []
    counts = df.groupby('status').size().reset_index(name='count')
    return counts.to_dict('records')


def get_daily_trend(df, days=30):
    """Get daily complaint count for last N days using Pandas"""
    if df.empty:
        return []

    end_date   = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # Filter last 30 days
    df_recent  = df[df['date'] >= start_date]

    # Group by date and count
    daily      = df_recent.groupby('date').size().reset_index(name='count')
    daily      = daily.sort_values('date')

    return [{'_id': str(row['date']), 'count': int(row['count'])} for _, row in daily.iterrows()]


def get_department_stats(df):
    """Calculate department performance using Pandas"""
    if df.empty:
        return []

    dept_stats = df.groupby('department').agg(
        total    = ('id', 'count'),
        resolved = ('is_resolved', 'sum'),
        avg_time = ('resolution_hours', 'mean')
    ).reset_index()

    dept_stats['resolution_rate'] = (dept_stats['resolved'] / dept_stats['total'] * 100).round(1)
    dept_stats['avg_time']        = dept_stats['avg_time'].round(1)
    dept_stats                    = dept_stats.sort_values('total', ascending=False)

    return dept_stats.to_dict('records')


def get_top_issues(df, n=5):
    """Get top N most upvoted unresolved issues using Pandas"""
    if df.empty:
        return []

    unresolved = df[df['status'] != 'resolved'].copy()
    top        = unresolved.nlargest(n, 'upvote_count')

    return top[['tracking_id', 'title', 'issue_type', 'priority', 'upvote_count', 'ward']].to_dict('records')


# ── MATPLOTLIB CHART GENERATORS ────────────────────────────────────────────────

def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                facecolor='#f0f4f0', edgecolor='none')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64


def generate_issue_type_chart(df):
    """Bar chart of issues by type using Matplotlib"""
    if df.empty:
        return None

    counts = df.groupby('issue_type').size().sort_values(ascending=True)
    colors = ['#1a6b3c'] * len(counts)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars    = ax.barh(counts.index, counts.values, color=colors, edgecolor='white', linewidth=0.5)

    # Add value labels
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontsize=10, color='#1a2e1a', fontweight='600')

    ax.set_xlabel('Number of Complaints', fontsize=11, color='#6b7f6b')
    ax.set_title('Complaints by Issue Type', fontsize=13, fontweight='bold', color='#1a2e1a', pad=15)
    ax.set_facecolor('#f0f4f0')
    fig.patch.set_facecolor('#f0f4f0')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors='#6b7f6b')
    plt.tight_layout()

    return fig_to_base64(fig)


def generate_priority_pie_chart(df):
    """Pie chart of issues by priority using Matplotlib"""
    if df.empty:
        return None

    counts = df.groupby('priority').size()
    colors = {'critical': '#ef4444', 'high': '#f97316', 'medium': '#eab308', 'low': '#22c55e'}
    clrs   = [colors.get(p, '#6b7280') for p in counts.index]

    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=counts.index, autopct='%1.1f%%',
        colors=clrs, startangle=90, pctdistance=0.85,
        wedgeprops=dict(edgecolor='white', linewidth=2)
    )
    for text in texts:
        text.set_color('#1a2e1a')
        text.set_fontsize(11)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')

    ax.set_title('Complaints by Priority', fontsize=13, fontweight='bold', color='#1a2e1a', pad=15)
    fig.patch.set_facecolor('#f0f4f0')
    plt.tight_layout()

    return fig_to_base64(fig)


def generate_daily_trend_chart(df, days=30):
    """Line chart of daily complaints using Matplotlib"""
    if df.empty:
        return None

    end_date   = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    df_recent  = df[df['date'] >= start_date].copy()

    if df_recent.empty:
        return None

    daily  = df_recent.groupby('date').size().reset_index(name='count')
    dates  = pd.to_datetime(daily['date'])
    counts = daily['count'].values

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(dates, counts, alpha=0.2, color='#1a6b3c')
    ax.plot(dates, counts, color='#1a6b3c', linewidth=2.5, marker='o', markersize=4)

    ax.set_xlabel('Date', fontsize=11, color='#6b7f6b')
    ax.set_ylabel('Complaints', fontsize=11, color='#6b7f6b')
    ax.set_title(f'Daily Complaint Trend (Last {days} Days)', fontsize=13, fontweight='bold', color='#1a2e1a', pad=15)
    ax.set_facecolor('#f0f4f0')
    fig.patch.set_facecolor('#f0f4f0')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors='#6b7f6b')
    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig_to_base64(fig)


def generate_ward_chart(df):
    """Horizontal bar chart of top affected wards"""
    if df.empty:
        return None

    ward_counts = df.groupby('ward').size().sort_values(ascending=False).head(8)
    colors      = plt.cm.Greens(np.linspace(0.4, 0.9, len(ward_counts)))[::-1]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars    = ax.barh(ward_counts.index, ward_counts.values, color=colors, edgecolor='white')

    for bar, val in zip(bars, ward_counts.values):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontsize=10, color='#1a2e1a', fontweight='600')

    ax.set_xlabel('Number of Complaints', fontsize=11, color='#6b7f6b')
    ax.set_title('Top Affected Wards', fontsize=13, fontweight='bold', color='#1a2e1a', pad=15)
    ax.set_facecolor('#f0f4f0')
    fig.patch.set_facecolor('#f0f4f0')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors='#6b7f6b')
    plt.tight_layout()

    return fig_to_base64(fig)


def generate_status_chart(df):
    """Donut chart of complaint statuses"""
    if df.empty:
        return None

    counts = df.groupby('status').size()
    colors_map = {
        'submitted':    '#ef4444',
        'acknowledged': '#3b82f6',
        'assigned':     '#8b5cf6',
        'in_progress':  '#f97316',
        'resolved':     '#22c55e',
        'rejected':     '#6b7280',
    }
    clrs = [colors_map.get(s, '#6b7280') for s in counts.index]

    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=counts.index, autopct='%1.0f%%',
        colors=clrs, startangle=90,
        wedgeprops=dict(width=0.6, edgecolor='white', linewidth=2)
    )
    for text in texts:
        text.set_color('#1a2e1a')
        text.set_fontsize(10)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(9)

    ax.set_title('Complaints by Status', fontsize=13, fontweight='bold', color='#1a2e1a', pad=15)
    fig.patch.set_facecolor('#f0f4f0')
    plt.tight_layout()

    return fig_to_base64(fig)
