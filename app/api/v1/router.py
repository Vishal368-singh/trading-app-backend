
from fastapi import APIRouter
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as user_router

api_router = APIRouter()

# Modules will be registered here
api_router.include_router(auth_router)
api_router.include_router(user_router)
# api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
# api_router.include_router(user_router, prefix="/users", tags=["Users"])
# api_router.include_router(research_router, prefix="/research", tags=["Research"])
# api_router.include_router(scanner_router, prefix="/scanner", tags=["Scanner"])
# api_router.include_router(algo_router, prefix="/algo", tags=["Algo"])
# api_router.include_router(paper_trading_router, prefix="/paper-trading", tags=["Paper Trading"])
