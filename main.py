import datetime
from prefect import Flow, task, context
from rich.table import Table
from rich.text import Text
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from textual import events
from textual.app import App
from textual.widgets import ScrollView
from typing import List, Tuple

class CustomScrollView(ScrollView):
    def move_left(self) -> None:
        self.target_x -= 2
        self.animate("x", self.target_x, speed=80, easing="out_cubic")

    def move_right(self) -> None:
        self.target_x += 2
        self.animate("x", self.target_x, speed=80, easing="out_cubic")

class MyApp(App):
    """An example of a very simple Textual App"""

    async def on_load(self, event: events.Load) -> None:
        await self.bind("q", "quit", "Quit")

    def on_key(self, event: events.Key):
        if event.key == 'left':
            self.body.move_left()
        elif event.key == 'right':
            self.body.move_right()

    async def on_mount(self, event: events.Mount) -> None:

        self.body = body = CustomScrollView(auto_width=True)

        await self.view.dock(body)

        async def add_content():
            table = Table(title="Resultado de busqueda")
        
            table.add_column(f'NRC', justify="center")
            table.add_column(f'Clave', justify="center")
            table.add_column(f'Materia', justify="center")
            table.add_column(f'Seccion', justify="center")
            table.add_column(f'Creditos', justify="center")
            table.add_column(f'Cupos Totales', justify="center")
            table.add_column(f'Cupos Disponibles', justify="center")
            table.add_column(f'Docente', justify="center")

            for i in range(len(MyApp.data)):
                table.add_row(*[Text(f"{MyApp.data[i][j].text}".strip()) for j in range(8)])

                
            await body.update(table)
                
        await self.call_later(add_content)

@task
def setup():
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(chrome_options=chrome_options, executable_path="/home/art/Documents/Tolerante/dataflow/chromedriver")
    
    return driver

@task(cache_for=datetime.timedelta(days=1))
def fetch_data(d: webdriver, s: str):
    d.get("http://consulta.siiau.udg.mx/wco/sspseca.forma_consulta")

    d.find_element(By.NAME, "ciclop").send_keys("202210")
    
    d.find_element(By.NAME, "cup").send_keys("D")
    
    d.find_element(By.NAME, "materiap").send_keys(s)
    
    d.find_element(By.ID, "idConsultar").click()
    
    data = d.find_elements(By.XPATH, "//td[@class='tddatos']")

    return data
    
@task(cache_for=datetime.timedelta(days=1))
def parse_data(elements: List):
    data = tuple(elements[x:x+8] for x in range(0, len(elements), 8))

    return data

@task
def get_input():
    s = input("INGRESA LA MATERIA A BUSCAR: ")
    return s
    
@task
def display_data(data: Tuple):
    MyApp.data = data
    MyApp.run(title="Consulta SIIAU", log="textual.log")

with Flow("Obteniendo informacion de SIIAU y mostrandola en la terminal") as r:
    driver = setup()
    i = get_input()
    raw_data = fetch_data(driver, i)
    parsed_data = parse_data(raw_data)
    z = display_data(parsed_data)
    
r.run()
