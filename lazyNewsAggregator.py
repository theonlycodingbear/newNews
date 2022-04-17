import datetime
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

import requests
from bs4 import BeautifulSoup
from newsapi import NewsApiClient
import sys

sys.excepthook = sys.__excepthook__


class News(tk.Tk):
    def __init__(self):
        super().__init__()
        # self.iconbitmap('icon/Folded-Newspaper.ico')  # must be in the same directory
        # self.iconbitmap('/home/ubu/00_Documents/01 Python projects/00 Up & running/newNews/icon/Folded-Newspaper.ico')
        # preparing flags-----------------------------------------------------------------------------------------------
        self.country = {}  # dictionary mapping flags to their path
        with open('list of countries.txt', encoding="ISO-8859-1") as f:  # must be in the same directory
            for line in f:
                (key, val) = line.split(', ')
                val = val.strip('\n')  # otherwise the \n stays in the string preventing the getting of the flag
                self.country[key] = val

        self.listOfFlags = []
        for e in os.listdir('flags'):  # must be in the same directory
            self.listOfFlags.append(e)
        # news api stuff------------------------------------------------------------------------------------------------
        self.api_key = '4ab491b6b6c54176bfd7341136d7aed2'
        self.newsapiClient = NewsApiClient(api_key=self.api_key)

        # initial geometry----------------------------------------------------------------------------------------------
        self.title('Lazy news aggregator')
        # self.geometry('800x600')
        self.state('normal')
        self.resizable(width=True, height=True)
        # Tkinter variables---------------------------------------------------------------------------------------------
        self.countrySelectionVariable = tk.StringVar()
        self.titleSelectionVariable = tk.StringVar()
        self.calls = tk.StringVar()
        self.caller = tk.StringVar()
        self.count = tk.IntVar()
        # Date ---------------------------------------------------------------------------------------------------------
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        # Main canvas---------------------------------------------------------------------------------------------------
        mainCanvasLeft = tk.Canvas(self, highlightthickness=0)
        mainCanvasLeft.grid(column=0, row=0, sticky='nsew', padx=10, pady=10)
        # LabelFrame: enter required elements to query the API----------------------------------------------------------
        infoFrame = ttk.LabelFrame(mainCanvasLeft, text='Enter required info:')
        infoFrame.grid(column=0, row=0, sticky='nsew')
        # meta canvas for the following two canvases--------------------------------------------------------------------
        self.metaCNV = tk.Canvas(infoFrame, highlightthickness=0)
        self.metaCNV.grid(column=0, row=0, sticky='nsew')
        # canvas for the country selection bit--------------------------------------------------------------------------
        self.countryCanvas = tk.Canvas(self.metaCNV, width=300, height=200, highlightthickness=0)
        self.countryCanvas.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')
        # canvas for the flags------------------------------------------------------------------------------------------
        self.flagDisplay = tk.Canvas(self.metaCNV, width=300, height=100, highlightthickness=0)
        self.flagDisplay.grid(column=0, row=1, padx=5, pady=5, sticky='nsew')
        # canvas for listboxes of outlets-------------------------------------------------------------------------------
        self.newsoutletCanvas = tk.Canvas(infoFrame, highlightthickness=0)
        self.newsoutletCanvas.grid(column=1, row=0, padx=5, pady=5, sticky='nsew')
        # various labels to be displayed--------------------------------------------------------------------------------
        self.countryLabel = ttk.Label(self.countryCanvas, text='Country:')
        self.countryLabel.grid(column=0, row=0, sticky='n', padx=10, pady=10)
        self.countryLabel.config(font=("courrier", 15))

        self.referencedNewsOutletsLabel = ttk.Label(self.newsoutletCanvas, text='Referenced News Outlets')
        self.referencedNewsOutletsLabel.grid(column=2, row=0, sticky='n')
        self.referencedNewsOutletsLabel.config(font=("courrier", 12))

        self.unreferencedNewsOutletsLabel = ttk.Label(self.newsoutletCanvas, text='Unreferenced News Outlets')
        self.unreferencedNewsOutletsLabel.grid(column=2, row=2, sticky='n')
        self.unreferencedNewsOutletsLabel.config(font=("courrier", 12))

        # country selection---------------------------------------------------------------------------------------------
        countries = []
        for e in self.country.keys():
            countries.append(e)
        self.placeFavorites(countries)  # puts the most frequently accessed countries on top of the list

        self.countrySelection = ttk.Combobox(self.countryCanvas, width=30, textvariable=self.countrySelectionVariable,
                                             values=countries)
        self.countrySelection.bind('<<ComboboxSelected>>', self.displayFlag, add="+")
        self.countrySelection.bind('<<ComboboxSelected>>', self.populateListReferencedSources, add="+")
        self.countrySelection.bind('<<ComboboxSelected>>', self.populateListUnreferencedSources, add="+")
        self.countrySelection.grid(column=1, row=0, sticky='n', padx=10, pady=10)

        # ListBox of referenced news outlet name------------------------------------------------------------------------
        self.referencedNewsOutletsListBox = tk.Listbox(self.newsoutletCanvas, width=40, height=4, selectmode='single')
        self.referencedNewsOutletsListBox.bind("<<ListboxSelect>>", lambda event: self.selection(event), add="+")
        self.referencedNewsOutletsListBox.bind("<<ListboxSelect>>",
                                               lambda event, org='referenced': self.getHeadlines(event, org), add="+")
        self.referencedNewsOutletsListBox.grid(column=2, row=1, sticky='n')
        self.referencedNewsOutletsListBox.config(bg='#80deea')

        # ListBox of unreferenced news outlet name----------------------------------------------------------------------
        self.unreferencedNewsOutletsListBox = tk.Listbox(self.newsoutletCanvas, width=40, height=4, selectmode='single')
        self.unreferencedNewsOutletsListBox.bind("<<ListboxSelect>>", lambda event: self.selection(event), add="+")
        self.unreferencedNewsOutletsListBox.bind("<<ListboxSelect>>",
                                                 lambda event, org='unreferenced': self.getHeadlines(event, org),
                                                 add="+")
        self.unreferencedNewsOutletsListBox.grid(column=2, row=3, sticky='n')
        self.unreferencedNewsOutletsListBox.config(bg='#f4ff81')

        # call counter, to show how many calls have been made so far (max = 300 per day)--------------------------------
        callCounterCanvas = tk.Canvas(infoFrame, highlightthickness=0)
        callCounterCanvas.grid(column=0, row=1, sticky='nsew', padx=5, pady=5)

        callCounterLabelFrame = tk.LabelFrame(callCounterCanvas, text='Good to know')
        callCounterLabelFrame.grid(column=0, row=0, sticky='nsew')

        self.callCounterLabel = ttk.Label(callCounterLabelFrame, text='Daily calls:')
        self.callCounterLabel.grid(column=0, row=0)
        self.callCounterLabel.config(font=("courrier", 15), anchor='center')

        self.callCounterShow = ttk.Label(callCounterLabelFrame, textvariable=self.calls)
        self.callCounterShow.grid(column=1, row=0)
        self.callCounterShow.config(font=("courrier", 20), anchor='center')

        # displays the title of the chosen news outlet------------------------------------------------------------------
        chosenTitleDisplay = ttk.Label(infoFrame, textvariable=self.titleSelectionVariable)
        chosenTitleDisplay.config(font=("courrier", 20), anchor="e")
        chosenTitleDisplay.grid(column=1, row=1, sticky='nsew')

        # canvas results------------------------------------------------------------------------------------------------
        resultCanvas = tk.Canvas(mainCanvasLeft, highlightthickness=0)
        resultCanvas.grid(column=0, row=1, sticky='nsew')

        # LabelFrame: returns the query results-------------------------------------------------------------------------
        resultFrame = ttk.LabelFrame(resultCanvas, text='Results:')
        resultFrame.grid(column=0, row=1, sticky='nsew', padx=10, pady=10)

        # query results-------------------------------------------------------------------------------------------------
        headlinesLabel = ttk.Label(resultFrame, text='Headlines:')
        headlinesLabel.config(font=("courrier", 15))
        headlinesLabel.grid(column=0, row=1, sticky='nsew', padx=10)

        # text widget to display the headlines--------------------------------------------------------------------------
        self.displayBox = tk.Text(resultFrame, width=60, wrap='word', height=15)
        self.displayBox.grid(column=0, row=3, ipadx=50, ipady=50, padx=10, pady=10, sticky='nsew')
        self.displayBox.tag_configure("even", background="#b3e5fc")
        self.displayBox.tag_configure("odd", background="#ffffff", font=("Courier", 10, 'italic'))

        # canvas to display article-------------------------------------------------------------------------------------
        articleCanvas = tk.Canvas(self, highlightthickness=0)
        articleCanvas.grid(column=1, row=0, padx=10, pady=10, sticky='nsew')

        articleLabel = ttk.Label(articleCanvas, text='Article:')
        articleLabel.config(font=("courrier", 18))
        articleLabel.grid(column=1, row=1, sticky='nsew', padx=10)

        # text widget to display the content of the article selected----------------------------------------------------
        self.displayArticle = tk.Text(articleCanvas, wrap='word', height=40)

        scrollbar = tk.Scrollbar(articleCanvas)  # not really useful, only shows how long the article is
        scrollbar.grid(column=2, row=2, sticky='nsew')
        scrollbar.config(command=self.displayArticle.yview)

        self.displayArticle.config(font=("courrier", 12))
        self.displayArticle.config(yscrollcommand=scrollbar.set, background='#ffecb3')
        # self.displayArticle.config(xscrollcommand=scrollbar.set, background='#ffecb3')
        self.displayArticle.grid(column=1, row=2, sticky='nsew')

        self.initialize_call_counter()  # to show the existing number of calls right after the start of the program

    def initialize_call_counter(self):  # initialize the data and keeps it up to date

        # db stuff
        connexion = sqlite3.connect('count_calls_news.db')
        cur = connexion.cursor()
        cmd = "SELECT COUNT from call_counter_news WHERE DATE=" + '"' + str(self.today) + '"'
        cur.execute(cmd)
        data = cur.fetchall()
        if not data:
            newRow = "INSERT INTO call_counter_news (DATE, COUNT) VALUES(" + '"' + str(self.today) + '"' + ',0)'
            cur.execute(newRow)
            connexion.commit()
            self.calls.set(0)
            self.count = 0
        else:
            dataToList = data  # turns tuple into list
            self.count = dataToList[0][0]  # extracts int from list
            self.calls.set(self.count)

    def displayFlag(self, event):  # shows a picture of the flag of the selected country
        self.flagDisplay.delete('all')
        self.titleSelectionVariable.set('')  # erases the previously chosen news outlet
        self.displayBox.config(state='normal')
        self.displayBox.delete('1.0', 'end')  # erases all previous headlines
        self.displayArticle.config(state='normal')
        self.displayArticle.delete('1.0', 'end')  # erases all previous text
        try:
            value = self.country.get(self.countrySelectionVariable.get()).lower() + '.png'
        except AttributeError:
            return

        if value in self.listOfFlags:
            imageX = tk.PhotoImage(file='flags/' + str(value))
        else:
            imageX = tk.PhotoImage(file='flags/' + '00 no flag.png')
        self.flagDisplay.image = imageX  # keep a reference, otherwise it's garbage collected!
        self.flagDisplay.create_image(150, 50, image=imageX)
        self.favorites()  # updates the list of favorite countries

    def populateListReferencedSources(self, event):
        self.referencedNewsOutletsListBox.delete(0, 'end')  # clears the ListBox of any previous value
        if self.countrySelectionVariable.get() == 5 * u'\u2015':
            return
        try:
            url = 'https://newsapi.org/v2/sources?apiKey=' + self.api_key  # valid for referenced sources, direct access
            referencedSources = requests.get(url).json()
            self.CallCounter()
        except ValueError:
            self.bell()
            messagebox.showinfo("Problem encountered", "Can not reach the server.\nTry again later.")
            sys.exit()

        self.nameToID = {}  # maps names in clear to id codes
        listOfAvailableReferencedSources = []
        for i in range(len(referencedSources.get('sources'))):
            country = referencedSources.get('sources')[i].get('country')
            if country == self.country.get(self.countrySelectionVariable.get()).lower():
                availableNames = referencedSources.get('sources')[i].get('name')
                if availableNames not in listOfAvailableReferencedSources:
                    listOfAvailableReferencedSources.append(availableNames)
                    self.nameToID.setdefault(availableNames, referencedSources.get('sources')[i].get('id'))

        listOfAvailableReferencedSources = sorted(listOfAvailableReferencedSources)

        for n in listOfAvailableReferencedSources:  # populates the ListBox with the names of news outlets
            self.referencedNewsOutletsListBox.insert('end', n)

    def populateListUnreferencedSources(self, event):
        self.unreferencedNewsOutletsListBox.delete(0, 'end')  # clears the ListBox of any previous value
        if self.countrySelectionVariable.get() == 5 * u'\u2015':
            return

        query = None
        sources = None
        category = None
        language = None
        country = self.country.get(self.countrySelectionVariable.get()).lower()
        # returns the headlines per country
        # generates an error in the shell if country is invalid, does not 'visibly' affect the program
        top_headlines = self.newsapiClient.get_top_headlines(q=query, sources=sources, category=category,
                                                             language=language, country=country)
        self.CallCounter()
        listOfAvailableTitles = []  # compilation of the names of news outlets per chosen country
        for i in range(len(top_headlines.get('articles'))):
            availableNames = top_headlines.get('articles')[i].get('source').get('name')
            if availableNames not in listOfAvailableTitles:
                listOfAvailableTitles.append(availableNames)

        compiledListOfAvailableTitles = sorted(listOfAvailableTitles)

        for n in compiledListOfAvailableTitles:  # populates the ListBox with the names of news outlets
            self.unreferencedNewsOutletsListBox.insert('end', n)

    def selection(self, event):  # identifies the element selected in ListBox of news outlets
        self.caller = event.widget
        self.idx = self.caller.curselection()
        if self.idx == ():  # to avoid error msg when choosing a new outlet
            # self.titleSelectionVariable.set('Nothing to show')
            return
        else:
            value = self.caller.get(self.idx)
            self.titleSelectionVariable.set(value)

    def getHeadlines(self, event, org):
        if self.idx == ():  # otherwise there is a subsequent call after a call to an unreferenced outlet / no idea why
            return  # seems to be a problem with the event

        self.displayBox.config(state='normal')
        self.displayBox.delete('1.0', 'end')  # erases all previous headlines
        self.displayArticle.config(state='normal')
        self.displayArticle.delete('1.0', 'end')  # erases all previous text
        self.compiledTitles = {}  # headlines per selected newspaper

        if org == 'referenced':
            query = None
            sources = self.nameToID.get(self.titleSelectionVariable.get())
            category = None
            language = None
            country = None

            headlinesReferencedOutlets = self.newsapiClient.get_top_headlines(q=query, sources=sources,
                                                                              category=category, language=language,
                                                                              country=country)
            self.CallCounter()

            headlinesList = headlinesReferencedOutlets.get('articles')
            for i in headlinesList:
                title = i.get('title')
                url = i.get('url')
                self.compiledTitles.setdefault(title, url)

        elif org == 'unreferenced':
            query = None
            sources = None
            category = None
            language = None
            country = self.country.get(self.countrySelectionVariable.get()).lower()

            headlinesUnreferencedOutlets = self.newsapiClient.get_top_headlines(q=query, sources=sources,
                                                                                category=category,
                                                                                language=language, country=country)
            self.CallCounter()

            headlinesList = headlinesUnreferencedOutlets.get('articles')
            for i in range(len(headlinesList)):
                outlet = headlinesList[i].get('source').get('name')
                if outlet == self.titleSelectionVariable.get():
                    title = str(headlinesList[i].get('title'))
                    url = str(headlinesList[i].get('url'))
                    self.compiledTitles.setdefault(title, url)

        tag = "odd"
        if self.compiledTitles == {}:
            self.displayBox.insert("end", 'NOTHING TO SHOW', tag)
        else:
            for line in self.compiledTitles:  # inserts headline in Text widget, and sets the line color
                self.displayBox.insert("end", line + '\n', tag)
                self.displayBox.tag_bind(tag, "<Button-1>", self.clicked)  # binds each entry to the method
                tag = "even" if tag == "odd" else "odd"

        self.displayBox.config(state='disabled')

    def clicked(self, event):
        self.displayArticle.config(state='normal')
        self.displayArticle.delete('1.0', 'end')  # erases all previous text
        lineClicked = self.displayBox.get('current linestart', 'current lineend')  # gets the content of clicked line

        for t in range(len(self.compiledTitles)):
            urlToOpen = self.compiledTitles.get(lineClicked)

        page = requests.get(urlToOpen)
        soup = BeautifulSoup(page.text, 'lxml')
        article = soup.find_all('p')

        for e in article:
            e = e.get_text()
            if len(e) < 60:  # to remove lines not related to the article, mildly effective, at best
                pass
            elif 'Article réservé à nos abonnés' in e:
                pass
            elif 'LIRE AUSSI' in e:
                pass
            elif 'VOIR AUSSI' in e:
                pass
            elif 'Click here' in e:
                pass
            elif '<<' in e:
                pass
            elif not (e[0:2]).isalnum():
                pass
            elif 'VIDÉO' in e:
                pass
            else:
                self.displayArticle.insert('end', e + '\n')
                self.displayArticle.tag_add('tatag', '1.0', 'end')
        self.displayArticle.tag_config('tatag', spacing1=5, spacing2=3, spacing3=5)

        self.displayArticle.insert('end', 'END OF THE ARTICLE')
        self.displayArticle.config(state='disabled')

    def CallCounter(self):
        connexion = sqlite3.connect('count_calls_news.db')
        cur = connexion.cursor()

        self.initialize_call_counter()  # to change the date if needed
        self.count += 1
        self.calls.set(self.count)
        update = "UPDATE call_counter_news SET COUNT=" + str(self.count) + ' WHERE DATE=' + '"' + str(self.today) + '"'
        cur.execute(update)
        connexion.commit()

    def favorites(self):
        connexion = sqlite3.connect('count_calls_news.db')
        cur = connexion.cursor()

        cmd = 'SELECT * FROM FAVORITES WHERE ID=' + '"' + self.countrySelectionVariable.get() + '"'
        cur.execute(cmd)
        data = cur.fetchall()

        if not data:
            cmd2 = 'INSERT INTO FAVORITES (ID, RANK) VALUES' + '("' + self.countrySelectionVariable.get() + '"' + ', 1)'
            cur.execute(cmd2)
            connexion.commit()
        else:
            cmd3 = 'UPDATE FAVORITES SET RANK=RANK+1 WHERE ID=' + '"' + self.countrySelectionVariable.get() + '"'
            cur.execute(cmd3)
            connexion.commit()

    def placeFavorites(self, countries):  # places the most often selected countries on top of the list
        connexion = sqlite3.connect('count_calls_news.db')
        cur = connexion.cursor()
        cmd = 'SELECT ID FROM FAVORITES ORDER BY RANK DESC, ID ASC'
        cur.execute(cmd)
        data = cur.fetchall()
        index = 0
        while index < 6:  # to limit the number of favourites to display
            if data[index][0] in countries:  # data[index] is a tuple
                countries.remove(data[index][0])
                countries.insert(index, data[index][0])
            index += 1
        countries.insert(index, 5 * (u'\u2015'))  # used as a separator in the listbox
        return countries


if __name__ == "__main__":
    app = News()
    app.mainloop()
