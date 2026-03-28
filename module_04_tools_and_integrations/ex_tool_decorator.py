# %%
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_function


# %%
@tool(return_direct=True)
def calculate_mortgage(
    principal: float,
    annual_rate: float,
    years: int,
    down_payment: float = 0.0,
) -> dict:
    """
    Рассчитать ежемесячный платёж по ипотеке.

    Используй эту функцию, когда пользователь спрашивает о расчёте
    ипотечного кредита, ежемесячных платежей или сравнении условий.

    Args:
        principal: Стоимость недвижимости в рублях
        annual_rate: Годовая процентная ставка (например, 12.5 для 12.5%)
        years: Срок кредита в годах
        down_payment: Первоначальный взнос в рублях (по умолчанию 0)

    Returns:
        Словарь с суммой кредита, ежемесячным платежом и общей переплатой
    """
    loan_amount = principal - down_payment
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12

    # Формула аннуитетного платежа
    if monthly_rate > 0:
        monthly_payment = (
            loan_amount
            * (monthly_rate * (1 + monthly_rate) ** num_payments)
            / ((1 + monthly_rate) ** num_payments - 1)
        )
    else:
        monthly_payment = loan_amount / num_payments

    total_paid = monthly_payment * num_payments

    return {
        "loan_amount": round(loan_amount, 2),
        "monthly_payment": round(monthly_payment, 2),
        "total_paid": round(total_paid, 2),
        "overpayment": round(total_paid - loan_amount, 2),
    }


# # %%
# openai_function = convert_to_openai_function(calculate_mortgage)
# print(openai_function)


# %%
tool_calculate_mortgage = tool(
    calculate_mortgage,
    description=calculate_mortgage.__doc__,
    return_direct=True,
)
print(tool_calculate_mortgage)
openai_function = convert_to_openai_function(tool_calculate_mortgage)
print(openai_function)
