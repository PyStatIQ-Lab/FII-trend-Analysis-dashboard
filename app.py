import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
from scipy.stats import pearsonr

# Configuration
API_URL = "https://oxide.sensibull.com/v1/compute/cache/fii_dii_daily"
CACHE_EXPIRY_DAYS = 1  # Refresh cache every day

# Load data function with caching
@st.cache_data(ttl=timedelta(days=CACHE_EXPIRY_DAYS))
def load_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return None

def process_data(raw_data):
    if not raw_data or 'data' not in raw_data:
        return pd.DataFrame()
    
    records = []
    
    for date, daily_data in raw_data['data'].items():
        record = {
            'date': date,
            'nifty': daily_data.get('nifty', None),
            'nifty_change_percent': daily_data.get('nifty_change_percent', None),
            'banknifty': daily_data.get('banknifty', None),
            'banknifty_change_percent': daily_data.get('banknifty_change_percent', None)
        }
        
        # Cash market data
        if 'cash' in daily_data:
            cash = daily_data['cash']
            if 'fii' in cash:
                fii_cash = cash['fii']
                record.update({
                    'fii_cash_buy': fii_cash.get('buy', None),
                    'fii_cash_sell': fii_cash.get('sell', None),
                    'fii_cash_net': fii_cash.get('buy_sell_difference', None),
                    'fii_cash_action': fii_cash.get('net_action', None),
                    'fii_cash_view': fii_cash.get('net_view', None),
                    'fii_cash_view_strength': fii_cash.get('net_view_strength', None)
                })
            
            if 'dii' in cash:
                dii_cash = cash['dii']
                record.update({
                    'dii_cash_buy': dii_cash.get('buy', None),
                    'dii_cash_sell': dii_cash.get('sell', None),
                    'dii_cash_net': dii_cash.get('buy_sell_difference', None),
                    'dii_cash_action': dii_cash.get('net_action', None),
                    'dii_cash_view': dii_cash.get('net_view', None),
                    'dii_cash_view_strength': dii_cash.get('net_view_strength', None)
                })
        
        # Futures data
        if 'future' in daily_data:
            future = daily_data['future']
            if 'fii' in future:
                fii_future = future['fii']
                if 'quantity-wise' in fii_future:
                    qty = fii_future['quantity-wise']
                    record.update({
                        'fii_future_net_oi': qty.get('net_oi', None),
                        'fii_future_action': qty.get('net_action', None),
                        'fii_future_view': qty.get('net_view', None),
                        'fii_future_view_strength': qty.get('net_view_strength', None)
                    })
                
                if 'amount-wise' in fii_future:
                    amt = fii_future['amount-wise']
                    record.update({
                        'fii_future_net_oi_amt': amt.get('net_oi', None),
                        'fii_future_view_amt': amt.get('net_view', None)
                    })
            
            if 'dii' in future:
                dii_future = future['dii']
                if 'quantity-wise' in dii_future:
                    qty = dii_future['quantity-wise']
                    record.update({
                        'dii_future_net_oi': qty.get('net_oi', None),
                        'dii_future_action': qty.get('net_action', None),
                        'dii_future_view': qty.get('net_view', None),
                        'dii_future_view_strength': qty.get('net_view_strength', None)
                    })
        
        # Options data
        if 'option' in daily_data:
            option = daily_data['option']
            if 'fii' in option:
                fii_option = option['fii']
                record.update({
                    'fii_option_overall_net_oi': fii_option.get('overall_net_oi', None),
                    'fii_option_action': fii_option.get('overall_net_oi_change_action', None),
                    'fii_option_view': fii_option.get('overall_net_oi_change_view', None),
                    'fii_option_view_strength': fii_option.get('overall_net_oi_change_view_strength', None)
                })
            
            if 'dii' in option:
                dii_option = option['dii']
                record.update({
                    'dii_option_overall_net_oi': dii_option.get('overall_net_oi', None),
                    'dii_option_action': dii_option.get('overall_net_oi_change_action', None),
                    'dii_option_view': dii_option.get('overall_net_oi_change_view', None),
                    'dii_option_view_strength': dii_option.get('overall_net_oi_change_view_strength', None)
                })
        
        records.append(record)
    
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date', ascending=True).reset_index(drop=True)
    
    # Calculate additional metrics
    if 'fii_cash_net' in df.columns:
        df['fii_cumulative_net'] = df['fii_cash_net'].cumsum()
    if 'dii_cash_net' in df.columns:
        df['dii_cumulative_net'] = df['dii_cash_net'].cumsum()
    
    return df

def calculate_correlations(df):
    correlations = {}
    if 'fii_cash_net' in df.columns and 'nifty_change_percent' in df.columns:
        corr, p_value = pearsonr(df['fii_cash_net'].dropna(), df['nifty_change_percent'].dropna())
        correlations['fii_net_vs_nifty'] = {'correlation': corr, 'p_value': p_value}
    
    if 'dii_cash_net' in df.columns and 'nifty_change_percent' in df.columns:
        corr, p_value = pearsonr(df['dii_cash_net'].dropna(), df['nifty_change_percent'].dropna())
        correlations['dii_net_vs_nifty'] = {'correlation': corr, 'p_value': p_value}
    
    return correlations

def show_historical_trends(df, metric, title, color):
    if metric not in df.columns:
        return
    
    df = df.sort_values('date', ascending=True)
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df[metric],
        name=title,
        line=dict(color=color, width=2),
        mode='lines+markers'
    ))
    
    if len(df) >= 7:
        df['7_day_ma'] = df[metric].rolling(7).mean()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['7_day_ma'],
            name='7-Day MA',
            line=dict(color='orange', width=2, dash='dot')
        ))
    
    if len(df) >= 30:
        df['30_day_ma'] = df[metric].rolling(30).mean()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['30_day_ma'],
            name='30-Day MA',
            line=dict(color='purple', width=2, dash='dot')
        ))
    
    fig.update_layout(
        title=f'{title} - Historical Trend',
        xaxis_title='Date',
        yaxis_title=title,
        hovermode='x unified',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_sentiment_analysis(df):
    if 'fii_cash_view' not in df.columns:
        return
    
    st.subheader("Sentiment Analysis")
    
    # Create sentiment columns
    df['fii_sentiment_score'] = df['fii_cash_view'].map({
        'BULLISH': 1,
        'BEARISH': -1,
        None: 0
    })
    
    df['dii_sentiment_score'] = df['dii_cash_view'].map({
        'BULLISH': 1,
        'BEARISH': -1,
        None: 0
    })
    
    # Sentiment over time
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['fii_sentiment_score'],
        name='FII Sentiment',
        line=dict(color='blue', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['dii_sentiment_score'],
        name='DII Sentiment',
        line=dict(color='green', width=2)
    ))
    fig.update_layout(
        title='Investor Sentiment Over Time',
        yaxis=dict(tickvals=[-1, 0, 1], ticktext=['Bearish', 'Neutral', 'Bullish']),
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Sentiment distribution
    col1, col2 = st.columns(2)
    with col1:
        if 'fii_cash_view' in df.columns:
            sentiment_counts = df['fii_cash_view'].value_counts()
            fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index, 
                         title='FII Sentiment Distribution')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'dii_cash_view' in df.columns:
            sentiment_counts = df['dii_cash_view'].value_counts()
            fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index, 
                         title='DII Sentiment Distribution')
            st.plotly_chart(fig, use_container_width=True)

def show_cumulative_flows(df):
    st.subheader("Cumulative Investment Flows")
    
    if 'fii_cumulative_net' in df.columns:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['fii_cumulative_net'],
            name='FII Cumulative Net',
            line=dict(color='blue', width=3)
        ))
        
        if 'dii_cumulative_net' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['dii_cumulative_net'],
                name='DII Cumulative Net',
                line=dict(color='green', width=3)
            ))
        
        fig.update_layout(
            title='Cumulative Net Investment (₹ Cr)',
            xaxis_title='Date',
            yaxis_title='Cumulative Amount (₹ Cr)',
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

def show_derivatives_analysis(df):
    st.subheader("Advanced Derivatives Analysis")
    
    if all(col in df.columns for col in ['fii_future_net_oi', 'fii_option_overall_net_oi']):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['fii_future_net_oi'],
            name='FII Futures OI',
            line=dict(color='orange', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['fii_option_overall_net_oi'],
            name='FII Options OI',
            line=dict(color='purple', width=2)
        ))
        fig.update_layout(
            title='FII Derivatives Exposure',
            xaxis_title='Date',
            yaxis_title='Net Open Interest',
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    if all(col in df.columns for col in ['fii_future_net_oi', 'nifty']):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['fii_future_net_oi'],
            y=df['nifty'],
            mode='markers',
            name='FII Futures vs Nifty',
            marker=dict(color='blue', size=8)
        ))
        fig.update_layout(
            title='FII Futures Positioning vs Nifty Levels',
            xaxis_title='FII Futures Net OI',
            yaxis_title='Nifty 50'
        )
        st.plotly_chart(fig, use_container_width=True)

def show_correlation_analysis(df):
    correlations = calculate_correlations(df)
    
    st.subheader("Correlation Analysis")
    
    if correlations:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("FII Net vs Nifty Returns Correlation", 
                      f"{correlations.get('fii_net_vs_nifty', {}).get('correlation', 0):.2f}",
                      help=f"P-value: {correlations.get('fii_net_vs_nifty', {}).get('p_value', 0):.4f}")
        
        with col2:
            st.metric("DII Net vs Nifty Returns Correlation", 
                      f"{correlations.get('dii_net_vs_nifty', {}).get('correlation', 0):.2f}",
                      help=f"P-value: {correlations.get('dii_net_vs_nifty', {}).get('p_value', 0):.4f}")
        
        # Correlation heatmap
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            fig = px.imshow(corr_matrix,
                          text_auto=True,
                          aspect="auto",
                          color_continuous_scale='RdBu',
                          range_color=[-1, 1])
            fig.update_layout(title='Correlation Matrix')
            st.plotly_chart(fig, use_container_width=True)

def show_volatility_analysis(df):
    if 'nifty_change_percent' not in df.columns:
        return
    
    st.subheader("Volatility Analysis")
    
    df['nifty_volatility'] = df['nifty_change_percent'].rolling(5).std() * np.sqrt(5)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['nifty_volatility'],
        name='Nifty 5-Day Volatility',
        line=dict(color='red', width=2)
    ))
    
    if 'fii_cash_net' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['fii_cash_net'].abs().rolling(5).mean(),
            name='FII Net Flow (5D Avg Absolute)',
            line=dict(color='blue', width=2),
            yaxis='y2'
        ))
    
    fig.update_layout(
        title='Market Volatility vs FII Flows',
        xaxis_title='Date',
        yaxis=dict(title='Volatility (%)'),
        yaxis2=dict(
            title='FII Net Flow (₹ Cr)',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.set_page_config(page_title="Advanced FII Analysis Dashboard", layout="wide")
    
    st.title("📈 Advanced FII/DII Analysis Dashboard")
    st.markdown("""
    <style>
    .big-font { font-size:18px !important; }
    </style>
    <p class="big-font">Comprehensive analysis of Foreign & Domestic Institutional Investor activities across cash, derivatives, and their market impact</p>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading market data..."):
        raw_data = load_data()
    
    if raw_data is None:
        st.error("Failed to load data. Please try again later.")
        return
    
    if 'last_updated' in raw_data:
        st.caption(f"Last updated: {raw_data['last_updated']}")
    
    df = process_data(raw_data)
    
    if df.empty:
        st.warning("No data available for the selected period.")
        return
    
    # Date range selector
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", min_date, min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.date_input("End date", max_date, min_value=min_date, max_value=max_date)
    
    # Filter and sort data
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].sort_values('date', ascending=True)
    
    # Dashboard sections
    show_key_metrics(filtered_df)
    show_historical_trends_section(filtered_df, df)
    show_cash_market_analysis(filtered_df)
    show_derivatives_analysis(filtered_df)
    show_sentiment_analysis(filtered_df)
    show_cumulative_flows(filtered_df)
    show_correlation_analysis(filtered_df)
    show_volatility_analysis(filtered_df)
    show_raw_data(filtered_df)

def show_key_metrics(filtered_df):
    st.subheader("📊 Key Metrics")
    
    cols = st.columns(5)
    metrics = [
        ('fii_cash_net', 'Latest FII Net (Cash)', '₹ Cr', None),
        ('dii_cash_net', 'Latest DII Net (Cash)', '₹ Cr', None),
        ('nifty', 'Nifty 50', '', 'nifty_change_percent'),
        ('banknifty', 'Bank Nifty', '', 'banknifty_change_percent'),
        ('fii_future_net_oi', 'FII Futures OI', 'Contracts', None)
    ]
    
    for i, (col, title, unit, change_col) in enumerate(metrics):
        if col in filtered_df.columns and len(filtered_df) > 0:
            value = filtered_df[col].iloc[-1]
            delta = None
            if change_col and change_col in filtered_df.columns:
                delta = f"{filtered_df[change_col].iloc[-1]:.2f}%"
            
            cols[i].metric(
                title,
                f"{value:,.2f}{unit}",
                delta=delta
            )

def show_historical_trends_section(filtered_df, full_df):
    st.subheader("📈 Historical Trends")
    
    tabs = st.tabs(["FII Activity", "DII Activity", "Market Indicators"])
    
    with tabs[0]:
        cols = st.columns(2)
        with cols[0]:
            show_historical_trends(filtered_df, 'fii_cash_net', 'FII Net Investment (Cash)', 'blue')
        with cols[1]:
            show_historical_trends(filtered_df, 'fii_future_net_oi', 'FII Futures OI', 'orange')
    
    with tabs[1]:
        cols = st.columns(2)
        with cols[0]:
            show_historical_trends(filtered_df, 'dii_cash_net', 'DII Net Investment (Cash)', 'green')
        with cols[1]:
            show_historical_trends(filtered_df, 'dii_future_net_oi', 'DII Futures OI', 'purple')
    
    with tabs[2]:
        cols = st.columns(2)
        with cols[0]:
            show_historical_trends(filtered_df, 'nifty', 'Nifty 50', 'red')
        with cols[1]:
            show_historical_trends(filtered_df, 'banknifty', 'Bank Nifty', 'gold')

def show_cash_market_analysis(filtered_df):
    st.subheader("💵 Cash Market Analysis")
    
    cols = st.columns(2)
    
    with cols[0]:
        if all(col in filtered_df.columns for col in ['fii_cash_buy', 'fii_cash_sell', 'fii_cash_net']):
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=filtered_df['date'],
                y=filtered_df['fii_cash_buy'],
                name='FII Buy',
                marker_color='green'
            ))
            fig.add_trace(go.Bar(
                x=filtered_df['date'],
                y=filtered_df['fii_cash_sell'],
                name='FII Sell',
                marker_color='red'
            ))
            fig.add_trace(go.Scatter(
                x=filtered_df['date'],
                y=filtered_df['fii_cash_net'],
                name='FII Net',
                mode='lines+markers',
                line=dict(color='blue', width=2)
            ))
            
            fig.update_layout(
                barmode='group',
                title='FII Cash Market Activity (₹ Cr)',
                xaxis_title='Date',
                yaxis_title='Amount (₹ Cr)',
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with cols[1]:
        if all(col in filtered_df.columns for col in ['fii_cash_net', 'dii_cash_net']):
            fig = px.line(filtered_df, x='date', y=['fii_cash_net', 'dii_cash_net'],
                         title='FII vs DII Net Investment (₹ Cr)')
            st.plotly_chart(fig, use_container_width=True)

def show_raw_data(filtered_df):
    st.subheader("📋 Raw Data")
    st.dataframe(filtered_df.sort_values('date', ascending=True), use_container_width=True)

if __name__ == "__main__":
    main()
