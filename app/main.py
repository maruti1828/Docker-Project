
import os
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import (
    DateTime,
    Integer,
    Numeric,
    String,
    create_engine,
    func,
    select,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://shoppulse:localdev123@localhost:5432/shoppulse",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    item: Mapped[str] = mapped_column(String(150), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="placed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    item: str = Field(min_length=1, max_length=150)
    quantity: int = Field(ge=1, le=1000)
    unit_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    item: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    status: str
    created_at: datetime


def get_db():
    with SessionLocal() as db:
        yield db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ShopPulse Order API",
    description="A beginner-friendly order management service.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "database": "unavailable"},
        )


@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    order = Order(
        customer_name=payload.customer_name.strip(),
        item=payload.item.strip(),
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        total_price=payload.unit_price * payload.quantity,
    )

    if not order.customer_name or not order.item:
        raise HTTPException(
            status_code=422,
            detail="Customer name and item cannot be blank.",
        )

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@app.get("/orders", response_model=list[OrderResponse])
def list_orders(db: Session = Depends(get_db)):
    statement = select(Order).order_by(Order.id.desc())
    return db.scalars(statement).all()


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return order

