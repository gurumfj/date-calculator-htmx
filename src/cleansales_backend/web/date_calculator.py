"""
Main application entry point
Uses MVC architecture with FastHTML
"""

import json
import uuid
from datetime import date, datetime, timedelta
from typing import Literal

from fasthtml.common import *

# tailwindcdn = Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4")

app, rt = fast_app(live=True)


@dataclass
class DateData:
    id: str
    base_date: date
    operation: str
    amount: int
    unit: str
    result: date

    def __post_init__(self):
        if self.operation not in ["before", "after"]:
            raise ValueError("wrong operation")
        elif self.unit not in ["days", "weeks", "months"]:
            raise ValueError("wrong unit")

    @classmethod
    def calculate_date(cls, data: "DateData") -> "DateData":
        if data.unit == "days":
            delta = timedelta(days=data.amount)
        elif data.unit == "weeks":
            delta = timedelta(weeks=data.amount)
        elif data.unit == "months":
            # More accurate month calculation
            if data.operation == "after":
                result_date = data.base_date
                for _ in range(data.amount):
                    if result_date.month == 12:
                        result_date = result_date.replace(year=result_date.year + 1, month=1)
                    else:
                        result_date = result_date.replace(month=result_date.month + 1)
                return cls(
                    id=str(uuid.uuid4()),
                    base_date=data.base_date,
                    operation=data.operation,
                    amount=data.amount,
                    unit=data.unit,
                    result=result_date,
                )
            else:
                result_date = data.base_date
                for _ in range(data.amount):
                    if result_date.month == 1:
                        result_date = result_date.replace(year=result_date.year - 1, month=12)
                    else:
                        result_date = result_date.replace(month=result_date.month - 1)
                return cls(
                    id=str(uuid.uuid4()),
                    base_date=data.base_date,
                    operation=data.operation,
                    amount=data.amount,
                    unit=data.unit,
                    result=result_date,
                )
        else:
            delta = timedelta(days=data.amount * 30)
        if data.operation == "after":
            result_date = data.base_date + delta
        else:
            result_date = data.base_date - delta
        return cls(
            id=str(uuid.uuid4()),
            base_date=data.base_date,
            operation=data.operation,
            amount=data.amount,
            unit=data.unit,
            result=result_date,
        )


class Viewer:
    def render_page(self):
        return Titled(
            "日期計算機",
            Body(
                self.render_date_picker(),
                self.render_result_section(),
            ),
        )

    def render_date_picker(self, data: DateData | None = None):
        pick_date_value = data.base_date if data else datetime.now().date()
        form = Form(
            Hidden(name="id", value=uuid.uuid4().hex),
            Hidden(name="result", value=None),
            Fieldset(
                Label(
                    "選擇日期",
                    Input(
                        type="date",
                        name="base_date",
                        value=pick_date_value,
                        required=True,
                    ),
                ),
                Group(
                    Label(
                        "間隔",
                        Input(
                            type="number",
                            name="amount",
                            min="1",
                            value=data.amount if data else 1,
                            required=True,
                        ),
                    ),
                    Label(
                        "單位",
                        Select(
                            Option("天", value="days", selected=data.unit == "days" if data else True),
                            Option("週", value="weeks", selected=data.unit == "weeks" if data else False),
                            Option("月", value="months", selected=data.unit == "months" if data else False),
                            name="unit",
                        ),
                    ),
                    style="gap: 10px",
                ),
            ),
            Group(
                Button(
                    "向前計算",
                    cls="form-button",
                    type="submit",
                    form="date-picker",
                    name="operation",
                    value="before",
                ),
                Button(
                    "向後計算",
                    cls="form-button",
                    type="submit",
                    form="date-picker",
                    name="operation",
                    value="after",
                ),
                style="gap: 10px;",
            ),
            id="date-picker",
            cls="form-group",
            method="post",
            action="#",
            hx_post="calculate",
            hx_target="#result-table-body",
            hx_swap="afterend",
        )

        if data:
            return fill_form(form, data)
        return form

    def render_result_section(self):
        return Div(
            Table(
                Thead(
                    Th("日期"),
                    Th("操作"),
                    Th("數量"),
                    Th("單位"),
                    Th("結果"),
                ),
                Tbody(
                    id="result-table-body"
                ),
            ),
            cls="overflow-auto",
        )

    def render_result_atom(self, date_data: "DateData"):
        def _pickup_btn(data: DateData, ask_result: bool = False):
            if ask_result and data.result:
                base_date = data.result
            else:
                base_date = data.base_date

            return Span(
                "↩️",
                hx_post="pickup",
                hx_vals=json.dumps(
                    {
                        "base_date": base_date.strftime("%Y-%m-%d"),
                        "operation": data.operation,
                        "amount": data.amount,
                        "unit": data.unit,
                        "id": data.id,
                        "result": "",
                    }
                ),
                hx_target=".form-group",
                hx_swap="outerHTML",
                style="cursor: pointer; margin-left: 5px;",
            )

        return Tr(
            Td(
                date_data.base_date.strftime("%Y-%m-%d"),
                _pickup_btn(date_data),
                name="base_date",
                value=date_data.base_date,
            ),
            Td(date_data.operation),
            Td(date_data.amount),
            Td(date_data.unit),
            Td(date_data.result.strftime("%Y-%m-%d"), _pickup_btn(date_data, True)),
            id="id_" + date_data.id,
        )

    def _comment(self, comment: str, children, **kwargs):
        return Safe("<!-- Start " + comment + " -->"), children, Safe("<!-- End " + comment + " -->")


class Controller:
    def __init__(self, viewer: Viewer):
        self.viewer = viewer

    def home(self):
        return self.viewer.render_page()

    def calculate(self, data: DateData):
        try:
            result = DateData.calculate_date(data)
            return self.viewer.render_result_atom(result)
        except ValueError:
            return Response("Invalid date calculation", status_code=400)

    def pickup(self, data: DateData):
        return self.viewer.render_date_picker(data)

    def validate_operation(self, operation: str) -> Literal["before", "after"]:
        match operation:
            case "before":
                return "before"
            case "after":
                return "after"
            case _:
                raise ValueError("Invalid operation")

    def validate_unit(self, unit: str) -> Literal["days", "weeks", "months"]:
        match unit:
            case "days":
                return "days"
            case "weeks":
                return "weeks"
            case "months":
                return "months"
            case _:
                raise ValueError("Invalid unit")


viewer = Viewer()
controller = Controller(viewer)


def setup_routes(app, rt):
    @rt("/")
    def get_home():
        return controller.home()

    @app.post("/calculate")
    def post(form: DateData):
        try:
            print(form)
            return controller.calculate(form)
        except ValueError:
            print("response 400")
            return Response("Invalid operation or unit", 400)

    @app.post("/pickup")
    def post_pickup(form: DateData):
        try:
            return controller.pickup(form)
        except ValueError:
            return "Invalid operation or unit", 400


setup_routes(app, rt)


def main():
    serve()


if __name__ == "__main__":
    main()
