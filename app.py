import pandas as pd
from math import floor
from lightweight_charts import Chart
import tkinter as tk
from tkinter import filedialog
from numpy import mean
from multiprocessing import Process , Queue

class CSVUploader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Upload CSV File")

        self.geometry("800x600")
        self.configure(bg="#f9f9f9")

        
        self.form_frame = tk.Frame(self, bg="#fff", padx=20, pady=20, bd=2, relief="solid")
        self.form_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.title_label = tk.Label(self.form_frame, text="Upload CSV File", font=("Arial", 18), bg="#fff", fg="#333")
        self.title_label.grid(row=0, column=0, columnspan=2, pady=10)

        self.file_label = tk.Label(self.form_frame, text="Choose CSV File:", bg="#fff")
        self.file_label.grid(row=1, column=0, sticky="w", pady=5)

        self.upload_button = tk.Button(self.form_frame, text="Upload", command=self.upload_csv, bg="#2E8B57", fg="#fff", padx=10, pady=5)
        self.upload_button.grid(row=1, column=1, sticky="w", pady=5)

        self.window_label = tk.Label(self.form_frame, text="Enter window size:", bg="#fff")
        self.window_label.grid(row=2, column=0, sticky="w", pady=5)

        self.window_entry = tk.Entry(self.form_frame, bg="#f9f9f9", bd=1, relief="solid")
        self.window_entry.grid(row=2, column=1, sticky="w", pady=5)

        self.tick_label = tk.Label(self.form_frame, text="Enter tick size:", bg="#fff")
        self.tick_label.grid(row=3, column=0, sticky="w", pady=5)

        self.tick_entry = tk.Entry(self.form_frame, bg="#f9f9f9", bd=1, relief="solid")
        self.tick_entry.grid(row=3, column=1, sticky="w", pady=5)

        self.upload_button = tk.Button(self.form_frame, text="Process", command=self.process_csv, bg="#2E8B57", fg="#fff", padx=10, pady=5)
        self.upload_button.grid(row=4, column=0, pady=10, sticky="we")

        self.best_button = tk.Button(self.form_frame, text="Best", command=self.process_best_csv, bg="#2E8B57", fg="#fff", padx=10, pady=5)
        self.best_button.grid(row=4, column=1, pady=10, sticky="we")

        self.form_frame.grid_columnconfigure(0, weight=1)
        self.form_frame.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(0, weight=1)

    def upload_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.csv_data = pd.read_csv(file_path)

    def process_csv(self):
        if hasattr(self, 'csv_data'):
            window = float(self.window_entry.get())
            tick = float(self.tick_entry.get())
            plot(self.csv_data , window , tick , chart_queue) 
        else:
            print("Please upload a CSV file first.")
  

    def process_best_csv(self):
        if hasattr(self, 'csv_data'):
            plot_best(self.csv_data , chart_queue)
        else:
            print("Please upload a CSV file first.")

def display_chart(queue):
    while True:
        chart_data = queue.get()
        if chart_data is None:
            break
        df = chart_data[1]
        chart = Chart()
        chart.set(df)
        method = chart_data[0]
        lines_data = chart_data[2]
        if method == 'plot_best':
            lo, hi, i, j = lines_data
            chart.trend_line(start_time=df.time[i] , end_time=df.time[j] , start_value=hi , end_value=hi , color='red')
            chart.trend_line(start_time=df.time[i] , end_time=df.time[j] , start_value=lo , end_value=lo , color='blue')
            chart.topbar.textbox('values' , initial_text=f"Width: {hi-lo} and length: {j-i} candles")
        elif method == 'plot':
            for  line in lines_data:
                i , j , h , c = line
                chart.trend_line(start_time=i , end_time=j , start_value=h , end_value=h , color=c)
            n = chart_data[3]
            sum = chart_data[4]
            if n:
                chart.topbar.textbox('Average' , initial_text=f'Average : {floor(sum/n)} candles')
            else:
                chart.topbar.textbox('Average' , initial_text='No range found')
        
        chart.show()



def calculate_adx(high, low, close, window=14):
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    plus_dm = (high - high.shift(1)).clip(lower=0)
    minus_dm = (low.shift(1) - low).clip(lower=0)
    
    atr = tr.ewm(span=window, min_periods=window).mean()
    plus_dm_smooth = plus_dm.ewm(span=window, min_periods=window).mean()
    minus_dm_smooth = minus_dm.ewm(span=window, min_periods=window).mean()

    plus_di = (plus_dm_smooth / atr) * 100
    minus_di = (minus_dm_smooth / atr) * 100

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100

    adx = dx.ewm(span=window, min_periods=2).mean()
    
    return adx


def plot_best(df , queue):
        df.index = pd.to_datetime(df.index)
        
        adx = calculate_adx(df.High, df.Low, df.Close) 

        chart = Chart()
        df = df.rename(columns={'High' : 'high' , 'Low' : 'low' , 'Close' : 'close' , 'Open' : 'open' , 'Timestamp (UTC)' : 'time'})
        chart.set(df)

        i = 14
        j = 14
        ct = 0
        longest_length = 0
        longest_line_data = None

        while(i < len(adx) and j < len(adx)):
            if adx[j] < 26:
                j = j + 1
            elif ct <= 1 or ct <= (j-i)/10:
                ct = ct + 1
                j = j + 1
            else:
                a = df.high[i:j+1]
                b = df.low[i:j+1]
                

                if ct == 0:
                    hi = a.nlargest(1).iloc[-1]  
                    lo = b.nsmallest(1).iloc[-1]
                    line_length = j - i
                    if line_length > longest_length:
                        longest_length = line_length
                        longest_line_data = (lo, hi, i, j)
                elif len(a) >= ct and len(b) >= ct:
                    hi = a.nlargest(ct).iloc[-1]  
                    lo = b.nsmallest(ct).iloc[-1]
                    line_length = j - i
                    if line_length > longest_length:
                        longest_length = line_length
                        longest_line_data = (lo, hi, i, j)
                ct = 0
                i = j

        if longest_line_data:
            lo, hi, i, j = longest_line_data
            chart.trend_line(start_time=df.time[i] , end_time=df.time[j] , start_value=hi , end_value=hi , color='red')
            chart.trend_line(start_time=df.time[i] , end_time=df.time[j] , start_value=lo , end_value=lo , color='blue')
            chart.topbar.textbox('values' , initial_text=f"Width: {hi-lo} and length: {j-i} candles")
        
        #chart.show()  
        queue.put(('plot_best' , df , longest_line_data))


def plot(df , window , tick , queue):

        df.index = pd.to_datetime(df.index)
        chart = Chart()
        df = df.rename(columns={'High' : 'high' , 'Low' : 'low' , 'Close' : 'close' , 'Open' : 'open' , 'Timestamp (UTC)' : 'time'})
        chart.set(df)
        
        adx = calculate_adx(df.high, df.low, df.close)

        i = 14
        j = 14
        ct = 0
        sum = 0
        n = 0
        plot_data = []
        while(i < len(adx) and j < len(adx)):
            if adx[j] < 26 and df.high[j] - df.low[j] - 2*tick <= window:
                j = j + 1
            elif ct <= 2 or ct <= (j-i)/10:
                ct = ct + 1
                j = j + 1
            else:
                a = df.high[i:j+1]
                b = df.low[i:j+1]
                if ct == 0:
                    hi = mean(a)
                    lo = mean(b)
                    mid = (hi+lo)/2
                    line_length = j - i
                    if line_length <= 2:
                        ct = 0
                        i = j
                        continue
                    # chart.trend_line(start_time=df.time[i] , end_time=df.time[j] , start_value=mid + window/2 , end_value=mid + window/2 , color='red')
                    # chart.trend_line(start_time=df.time[i] , end_time=df.time[j] , start_value=mid - window/2 , end_value=mid - window/2 , color='blue')
                    list_1 = [df.time[i] , df.time[j] , mid+window/2 , 'red']
                    plot_data.append(list_1)
                    list_2 = [df.time[i] , df.time[j] , mid-window/2 , 'blue']
                    plot_data.append(list_2)                   
                    n = n+1
                    n = n+1
                    sum = sum + line_length
                elif len(a) >= ct and len(b) >= ct:
                    hi = mean(a)
                    lo = mean(b)
                    mid = (hi+lo)/2
                    line_length = j - i
                    if line_length <= 2:
                        ct = 0
                        i = j
                        continue
                    # chart.trend_line(start_time=df.time[i] , end_time=df.time[j] , start_value=mid + window/2 , end_value=mid + window/2 , color='red')
                    # chart.trend_line(start_time=df.time[i] , end_time=df.time[j] , start_value=mid - window/2 , end_value=mid - window/2 , color='blue')
                    list_1 = [df.time[i] , df.time[j] , mid+window/2 , 'red']
                    plot_data.append(list_1)
                    list_2 = [df.time[i] , df.time[j] , mid-window/2 , 'blue']
                    plot_data.append(list_2)
                    n = n+1
                    sum = sum + line_length             
                ct = 0
                i = j
        # if n:
        #     chart.topbar.textbox('Average' , initial_text=f'Average : {floor(sum/n)} candles')
        # else:
        #     chart.topbar.textbox('Average' , initial_text='No range found')

        # chart.show(block=True)
        queue.put(('plot' , df , plot_data , n , sum))
  

if __name__ == "__main__":
    app = CSVUploader()
    chart_queue = Queue()
    chart_process = Process(target=display_chart , args=(chart_queue,))

    try:
        chart_process.start()
        app.mainloop()
    except Exception as e:
        print("An error occured in the main process:" , e)
    finally:
        chart_queue.put(None)
        chart_process.join()