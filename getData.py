import pandas as pd
from langchain_community.llms import Ollama
from pydantic import BaseModel, field_validator
from typing import List

def hop(start, stop, step):
    for i in range(start, stop, step):
        yield i
    yield stop

class ResponseChecks(BaseModel):
    data: List[str]

    @field_validator("data")
    def check(cls, value):
        for item in value:
            if len(item) > 0:
                assert "-" in item, "String does not contain hyphen."

def categorize_transactions(transaction_names, llm):
    prompt = (
        "Can you add an appropriate category to the following expenses. "
        "For example: Spotify AB by Adyen - Entertainment, Beta Boulders Ams Amsterdam Nld - Sport, etc.. "
        "Categories should be less than 4 words. " + transaction_names
    )
    response = llm.invoke(prompt)
    response = response.split('\n')
    blank_indexes = [i for i, line in enumerate(response) if line == '']
    if len(blank_indexes) == 1:
        response = response[(blank_indexes[0] + 1):]
    else:
        response = response[(blank_indexes[0] + 1): blank_indexes[1]]
    print(response)
    ResponseChecks(data=response)
    categories_df = pd.DataFrame({'Transaction vs category': response})
    categories_df[['Transaction', 'Category']] = categories_df['Transaction vs category'].str.split(' - ', expand=True)
    return categories_df

def clean_and_merge_categories(df, categories_df_all):
    categories_df_all = categories_df_all.dropna()
    categories_df_all.loc[categories_df_all['Category'].str.contains("Food"), 'Category'] = "Food and Drinks"
    categories_df_all.loc[categories_df_all['Category'].str.contains("Clothing"), 'Category'] = "Clothing"
    categories_df_all.loc[categories_df_all['Category'].str.contains("Services"), 'Category'] = "Services"
    categories_df_all.loc[categories_df_all['Category'].str.contains("Health|Wellness"), 'Category'] = "Health and Wellness"
    categories_df_all.loc[categories_df_all['Category'].str.contains("Sport"), 'Category'] = "Sport and Fitness"
    categories_df_all.loc[categories_df_all['Category'].str.contains("Travel"), 'Category'] = "Travel"
    categories_df_all['Transaction'] = categories_df_all['Transaction'].str.replace(r'\d+\.\s+', '', regex=True)
    df.loc[df['Name / Description'].str.contains("Spotify"), 'Name / Description'] = "Spotify Ab By Adyen"
    merged_df = pd.merge(df, categories_df_all, left_on='Name / Description', right_on='Transaction', how='left')
    return merged_df

def main():
    llm = Ollama(model="llama2")
    df = pd.read_csv("data/transactions_2022_2023.csv")
    unique_transactions = df["Name / Description"].unique()
    index_list = list(hop(0, len(unique_transactions), 30))
    categories_df_all = pd.DataFrame()
    max_tries = 7

    for i in range(0, len(index_list) - 1):
        transaction_names = unique_transactions[index_list[i]:index_list[i + 1]]
        transaction_names = ','.join(transaction_names)
        for j in range(1, max_tries):
            try:
                categories_df = categorize_transactions(transaction_names, llm)
                categories_df_all = pd.concat([categories_df_all, categories_df], ignore_index=True)
            except Exception:
                if j < max_tries:
                    continue
                else:
                    raise Exception(f"Cannot categorise transactions indexes {i} to {i + 1}.")
            break

    merged_df = clean_and_merge_categories(df, categories_df_all)
    merged_df.to_csv("data/transactions_2022_2023_categorized.csv", index=False)

if __name__ == "__main__":
    main()