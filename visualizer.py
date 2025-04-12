import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def plot_spending_by_category(data):
    """
    Create a pie chart of spending by category.
    
    Args:
        data (pd.DataFrame): DataFrame containing categorized transaction data
        
    Returns:
        plotly.graph_objects.Figure: Pie chart figure
    """
    # Group data by category and sum amounts
    category_totals = data.groupby('Category')['Amount'].sum().reset_index()
    
    # Create pie chart
    fig = px.pie(
        category_totals,
        values='Amount',
        names='Category',
        title='Spending by Category',
        hole=0.4,  # Donut chart
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    
    # Update layout
    fig.update_layout(
        legend_title="Categories",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    # Add total in the center
    total_spend = category_totals['Amount'].sum()
    fig.add_annotation(
        text=f"${total_spend:.2f}<br>Total",
        x=0.5, y=0.5,
        font=dict(size=14, color="black", family="Arial, sans-serif"),
        showarrow=False
    )
    
    return fig


def plot_spending_over_time(data):
    """
    Create a line chart of spending over time by category.
    
    Args:
        data (pd.DataFrame): DataFrame containing categorized transaction data
        
    Returns:
        plotly.graph_objects.Figure: Line chart figure
    """
    # Ensure date is datetime format
    data['Date'] = pd.to_datetime(data['Date'])
    
    # Group by month and category
    monthly_data = data.copy()
    monthly_data['Month'] = monthly_data['Date'].dt.strftime('%Y-%m')
    monthly_category = monthly_data.groupby(['Month', 'Category'])['Amount'].sum().reset_index()
    
    # Create line chart
    fig = px.line(
        monthly_category,
        x='Month',
        y='Amount',
        color='Category',
        markers=True,
        title='Monthly Spending by Category',
        labels={'Month': 'Month', 'Amount': 'Amount ($)', 'Category': 'Category'}
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        legend_title="Categories",
        hovermode="x unified"
    )
    
    # Add total spending line
    monthly_total = monthly_data.groupby('Month')['Amount'].sum().reset_index()
    fig.add_trace(
        go.Scatter(
            x=monthly_total['Month'],
            y=monthly_total['Amount'],
            mode='lines+markers',
            name='Total',
            line=dict(color='black', width=3, dash='dot'),
            marker=dict(size=10)
        )
    )
    
    return fig


def plot_spending_heatmap(data):
    """
    Create a heatmap of spending by category and month.
    
    Args:
        data (pd.DataFrame): DataFrame containing categorized transaction data
        
    Returns:
        plotly.graph_objects.Figure: Heatmap figure
    """
    # Ensure date is datetime format
    data['Date'] = pd.to_datetime(data['Date'])
    
    # Extract month and year
    data['Month'] = data['Date'].dt.strftime('%Y-%m')
    
    # Create pivot table
    pivot = pd.pivot_table(
        data,
        values='Amount',
        index='Category',
        columns='Month',
        aggfunc='sum',
        fill_value=0
    )
    
    # Sort columns chronologically
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)
    
    # Create heatmap
    fig = px.imshow(
        pivot,
        labels=dict(x="Month", y="Category", color="Amount ($)"),
        x=pivot.columns,
        y=pivot.index,
        color_continuous_scale='YlGnBu',
        title='Monthly Spending Heatmap by Category'
    )
    
    # Add text annotations
    for i, category in enumerate(pivot.index):
        for j, month in enumerate(pivot.columns):
            value = pivot.loc[category, month]
            fig.add_annotation(
                x=month, 
                y=category,
                text=f"${value:.2f}",
                showarrow=False,
                font=dict(color="black" if value < pivot.values.max()/2 else "white")
            )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Category",
        coloraxis_colorbar=dict(title="Amount ($)")
    )
    
    return fig
