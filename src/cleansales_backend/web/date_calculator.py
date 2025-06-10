"""
Main application entry point
Uses MVC architecture with FastHTML
"""

import json
import uuid
from datetime import date, datetime, timedelta
from typing import Literal, Optional

from fasthtml.common import *

# tailwindcdn = Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4")
app, rt = fast_app(live=True)


class Viewer:
    def render_page(self):
        return Titled(
            "日期計算機",
            Body(
                self.render_date_picker(),
                self.render_result_section(),
            ),
        )

    def render_date_picker(self, data: Optional["DateData"] = None):
        if data:
            base_date = data.result.strftime("%Y-%m-%d")
        else:
            base_date = date.today().strftime("%Y-%m-%d")
        return Form(
            Label("選擇日期:", cls="form-label"),
            Input(type="date", name="base_date", value=base_date, required=True, cls="form-input"),
            Input(
                type="number", name="amount", min="1", value=data.amount if data else 1, required=True, cls="form-input"
            ),
            Select(
                Option("天", value="days", selected=data.unit == "days" if data else True),
                Option("週", value="weeks", selected=data.unit == "weeks" if data else False),
                Option("月", value="months", selected=data.unit == "months" if data else False),
                name="unit",
                cls="form-select",
            ),
            Group(
                Button(
                    "向前計算",
                    cls="form-button",
                    type="submit",
                    form="date-picker",
                    hx_post="calculate/before",
                    hx_target="#result-table-body",
                    hx_swap="afterend",
                ),
                Button(
                    "向後計算",
                    cls="form-button",
                    type="submit",
                    form="date-picker",
                    hx_post="calculate/after",
                    hx_target="#result-table-body",
                    hx_swap="afterend",
                ),
                style="gap: 10px;",
            ),
            cls="form-group",
        )

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
                    # render result atom
                    id="result-table-body"
                ),
            ),
        )

    def render_result_atom(self, date_data: "DateData"):
        def _pickup_btn(base_date: date, id: str):
            return Span(
                "↩️",
                hx_post="pickup",
                hx_vals=json.dumps(
                    {
                        "pickup_date": base_date.strftime("%Y-%m-%d"),
                        "operation": date_data.operation,
                        "amount": date_data.amount,
                        "unit": date_data.unit,
                        "id": id,
                    }
                ),
                hx_target=".form-group",
                hx_swap="outerHTML",
                style="cursor: pointer; margin-left: 5px;",
            )

        return Tr(
            Td(date_data.base_date.strftime("%Y-%m-%d"), _pickup_btn(date_data.base_date, date_data.id)),
            Td(date_data.operation),
            Td(date_data.amount),
            Td(date_data.unit),
            Td(date_data.result.strftime("%Y-%m-%d"), _pickup_btn(date_data.result, date_data.id)),
        )

    def _comment(self, comment: str, children, **kwargs):
        return Safe("<!-- Start " + comment + " -->"), children, Safe("<!-- End " + comment + " -->")


@dataclass
class DateData:
    id: str
    base_date: date
    operation: Literal["after", "before"]
    amount: int
    unit: Literal["days", "weeks", "months"]
    result: date

    @classmethod
    def calculate_date(
        cls,
        base_date: date,
        operation: Literal["after", "before"],
        amount: int,
        unit: Literal["days", "weeks", "months"],
    ) -> "DateData":
        if unit == "days":
            delta = timedelta(days=amount)
        elif unit == "weeks":
            delta = timedelta(weeks=amount)
        elif unit == "months":
            delta = timedelta(days=amount * 30)
        if operation == "after":
            result_date = base_date + delta
        else:
            result_date = base_date - delta
        return cls(
            id=str(uuid.uuid4()),
            base_date=base_date,
            operation=operation,
            amount=amount,
            unit=unit,
            result=result_date,
        )


class Controller:
    def __init__(self, viewer: Viewer):
        self.viewer = viewer

    def home(self):
        return self.viewer.render_page()

    def calculate(
        self,
        base_date: str,
        operation: Literal["before", "after"],
        amount: int,
        unit: Literal["days", "weeks", "months"],
    ):
        _base_date = datetime.strptime(base_date, "%Y-%m-%d").date()
        result = DateData.calculate_date(_base_date, operation, amount, unit)
        return self.viewer.render_result_atom(result)

    def pickup(
        self,
        pickup_date: str,
        operation: Literal["before", "after"],
        amount: int,
        unit: Literal["days", "weeks", "months"],
        id: str,
    ):
        _pickup_date = datetime.strptime(pickup_date, "%Y-%m-%d").date()
        return self.viewer.render_date_picker(
            DateData(id=id, base_date=_pickup_date, operation=operation, amount=amount, unit=unit, result=_pickup_date)
        )

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

    @rt("/calculate/{operation}")
    def post_calculate(base_date: str, operation: str, amount: int, unit: str):
        try:
            _operation = controller.validate_operation(operation)
            _unit = controller.validate_unit(unit)
            return controller.calculate(base_date, _operation, amount, _unit)
        except ValueError:
            return "Invalid operation or unit", 400

    @rt("/pickup")
    def post_pickup(pickup_date: str, operation: str, amount: int, unit: str, id: str):
        try:
            _operation = controller.validate_operation(operation)
            _unit = controller.validate_unit(unit)
            return controller.pickup(pickup_date, _operation, amount, _unit, id)
        except ValueError:
            return "Invalid operation or unit", 400

    @rt("/pickup")
    def get_pickup(pickup_date: str, operation: str, amount: int, unit: str, id: str):
        try:
            _operation = controller.validate_operation(operation)
            _unit = controller.validate_unit(unit)
            return controller.pickup(pickup_date, _operation, amount, _unit, id)
        except ValueError:
            return "Invalid operation or unit", 400


setup_routes(app, rt)


def main():
    serve()


if __name__ == "__main__":
    main()
