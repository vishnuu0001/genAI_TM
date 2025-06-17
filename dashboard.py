import pandas as pd
import numpy as np
import plotly.express as px
import panel as pn

def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)
    df['Year'] = pd.to_datetime(df['Date']).dt.year
    df['Month'] = pd.to_datetime(df['Date']).dt.month
    df['Month Name'] = pd.to_datetime(df['Date']).dt.strftime("%b")
    df = df.drop(columns=['Transaction', 'Transaction vs category'])
    df['Category'] = np.where(df['Expense/Income'] == 'Income', df['Name / Description'], df['Category'])
    return df

def make_pie_chart(df, year, label):
    sub_df = df[(df['Expense/Income'] == label) & (df['Year'] == year)]
    color_scale = px.colors.qualitative.Set2
    pie_fig = px.pie(sub_df, values='Amount (EUR)', names='Category', color_discrete_sequence=color_scale)
    pie_fig.update_traces(textposition='inside', direction='clockwise', hole=0.3, textinfo="label+percent")
    total_expense = df[(df['Expense/Income'] == 'Expense') & (df['Year'] == year)]['Amount (EUR)'].sum()
    total_income = df[(df['Expense/Income'] == 'Income') & (df['Year'] == year)]['Amount (EUR)'].sum()
    if label == 'Expense':
        total_text = "€ " + str(round(total_expense))
        saving_rate = round((total_income - total_expense) / total_income * 100)
        saving_rate_text = ": Saving rate " + str(saving_rate) + "%"
    else:
        saving_rate_text = ""
        total_text = "€ " + str(round(total_income))
    pie_fig.update_layout(
        uniformtext_minsize=10,
        uniformtext_mode='hide',
        title=dict(text=label + " Breakdown " + str(year) + saving_rate_text),
        annotations=[
            dict(
                text=total_text,
                x=0.5, y=0.5, font_size=12,
                showarrow=False
            )
        ]
    )
    return pie_fig

def make_monthly_bar_chart(df, year, label):
    sub_df = df[(df['Expense/Income'] == label) & (df['Year'] == year)]
    total_by_month = (sub_df.groupby(['Month', 'Month Name'])['Amount (EUR)'].sum()
                      .to_frame()
                      .reset_index()
                      .sort_values(by='Month')
                      .reset_index(drop=True))
    color_scale = px.colors.sequential.YlGn if label == "Income" else px.colors.sequential.OrRd
    bar_fig = px.bar(
        total_by_month, x='Month Name', y='Amount (EUR)', text_auto='.2s',
        title=label + " per month", color='Amount (EUR)', color_continuous_scale=color_scale
    )
    return bar_fig

def create_tabs(df):
    tabs = pn.Tabs(
        ('2022', pn.Column(
            pn.Row(make_pie_chart(df, 2022, 'Income'), make_pie_chart(df, 2022, 'Expense')),
            pn.Row(make_monthly_bar_chart(df, 2022, 'Income'), make_monthly_bar_chart(df, 2022, 'Expense'))
        )),
        ('2023', pn.Column(
            pn.Row(make_pie_chart(df, 2023, 'Income'), make_pie_chart(df, 2023, 'Expense')),
            pn.Row(make_monthly_bar_chart(df, 2023, 'Income'), make_monthly_bar_chart(df, 2023, 'Expense'))
        ))
    )
    return tabs

def create_dashboard(tabs):
    template = pn.template.FastListTemplate(
        title='Personal Finance Dashboard',
        sidebar=[
            pn.pane.Markdown("# Income Expense analysis"),
            pn.pane.Markdown("Overview of income and expense based on my bank transactions. Categories are obtained using local LLMs."),
            pn.pane.PNG("picture.png", sizing_mode="scale_both")
        ],
        main=[pn.Row(pn.Column(pn.Row(tabs)))],
        header_background="#c0b9dd",
    )
    return template

def main():
    pn.extension('plotly')
    df = load_and_prepare_data('data/transactions_2022_2023_categorized.csv')
    tabs = create_tabs(df)
    tabs.show()
    dashboard = create_dashboard(tabs)
    dashboard.show()

if __name__ == "__main__":
    main()