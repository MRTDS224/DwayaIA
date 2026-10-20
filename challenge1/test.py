import pandas as pd
df = pd.DataFrame({'Priorité': ['Moyenne', 'Basse', 'Haute', None, 'Basse']})
categories_avec_nan = ['Inconnu', 'Basse', 'Moyenne', 'Haute']
df['Priorité'] = df['Priorité'].fillna('Inconnu')
df['Priorité'] = pd.Categorical(df['Priorité'], categories=categories_avec_nan, ordered=True)
df['Priorité_Encoded'] = df['Priorité'].cat.codes
print(df)

df = pd.DataFrame({'Ville': ['Paris', 'Lyon', 'Marseille', 'Paris', None]})
df_encoded = pd.get_dummies(df, columns=['Ville'], dummy_na=True, drop_first=True)
print(df_encoded)