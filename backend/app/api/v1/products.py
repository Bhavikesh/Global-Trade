"""
Product routes — /api/v1/organizations/{organization_id}/products

POST   ""                               — create product
GET    ""                               — list products (search by q, filter by status)
GET    "/{product_id}"                  — get single product
PATCH  "/{product_id}"                  — update product
DELETE "/{product_id}"                  — delete product
POST   "/{product_id}/files"            — attach file to product
GET    "/{product_id}/files"            — list product files
DELETE "/{product_id}/files/{file_id}"  — remove product file
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.auth.permissions import (
    get_membership_or_403,
    require_organization_membership,
)
from app.db.session import get_db
from app.models.product import Product, ProductFile
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductFileCreate,
    ProductFileRead,
    ProductRead,
    ProductUpdate,
)

router = APIRouter(prefix="/organizations/{organization_id}/products", tags=["Products"])


def _get_product_or_404(product_id: uuid.UUID, organization_id: uuid.UUID, db: Session) -> Product:
    product = db.query(Product).filter_by(id=product_id, organization_id=organization_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
)
def create_product(
    organization_id: uuid.UUID,
    body: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductRead:
    require_organization_membership(organization_id, current_user, db)

    # Exclude organization_id from body to strictly enforce URL origin
    create_data = body.model_dump(exclude={"organization_id"})
    product = Product(
        organization_id=organization_id,
        **create_data,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get(
    "",
    response_model=List[ProductRead],
    summary="List products for an organization",
)
def list_products(
    organization_id: uuid.UUID,
    q: Optional[str] = Query(None, description="Search term for name and keywords"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, ARCHIVED)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ProductRead]:
    get_membership_or_403(organization_id, current_user, db)

    query = db.query(Product).filter_by(organization_id=organization_id)
    if q and q.strip():
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(search),
                Product.keywords.ilike(search),
            )
        )
    if status:
        query = query.filter(Product.status == status)

    return query.all()


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Get a product by ID",
)
def get_product(
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductRead:
    get_membership_or_403(organization_id, current_user, db)
    return _get_product_or_404(product_id, organization_id, db)


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    summary="Update a product",
)
def update_product(
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    body: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductRead:
    require_organization_membership(organization_id, current_user, db)
    product = _get_product_or_404(product_id, organization_id, db)

    update_data = body.model_dump(exclude_unset=True, exclude={"id", "organization_id"})
    for field, value in update_data.items():
        setattr(product, field, value)

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
)
def delete_product(
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    require_organization_membership(organization_id, current_user, db)
    product = _get_product_or_404(product_id, organization_id, db)

    db.delete(product)
    db.commit()


@router.post(
    "/{product_id}/files",
    response_model=ProductFileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Attach a file to a product",
)
def add_product_file(
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    body: ProductFileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductFileRead:
    require_organization_membership(organization_id, current_user, db)
    _get_product_or_404(product_id, organization_id, db)

    # Exclude organization_id and product_id to prevent collision with URL params
    file_data = body.model_dump(exclude={"organization_id", "product_id"})
    product_file = ProductFile(
        product_id=product_id,
        organization_id=organization_id,
        **file_data,
    )
    db.add(product_file)
    db.commit()
    db.refresh(product_file)
    return product_file


@router.get(
    "/{product_id}/files",
    response_model=List[ProductFileRead],
    summary="List files for a product",
)
def list_product_files(
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ProductFileRead]:
    get_membership_or_403(organization_id, current_user, db)
    _get_product_or_404(product_id, organization_id, db)

    return (
        db.query(ProductFile)
        .filter_by(product_id=product_id, organization_id=organization_id)
        .all()
    )


@router.delete(
    "/{product_id}/files/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product file",
)
def delete_product_file(
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    require_organization_membership(organization_id, current_user, db)
    _get_product_or_404(product_id, organization_id, db)

    product_file = (
        db.query(ProductFile)
        .filter_by(id=file_id, product_id=product_id, organization_id=organization_id)
        .first()
    )
    if product_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product file not found.",
        )

    db.delete(product_file)
    db.commit()