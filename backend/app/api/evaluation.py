from fastapi import APIRouter


router = APIRouter()


@router.post("/run")
async def run_evaluation(test_suite: str):
    # TODO: 实现评估运行
    return {"eval_id": "test-eval-id", "status": "running"}


@router.get("/result/{eval_id}")
async def get_evaluation_result(eval_id: str):
    # TODO: 实现评估结果查询
    return {
        "eval_id": eval_id,
        "status": "completed",
        "score": 0.85,
        "total_cases": 100,
        "passed_cases": 85
    }
