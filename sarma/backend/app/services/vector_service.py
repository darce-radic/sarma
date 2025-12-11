"""
Vector Embedding and Semantic Search Service
"""
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.recipe import Recipe


class VectorSearchService:
    """Service for vector embeddings and semantic search"""
    
    @staticmethod
    async def generate_recipe_embedding(
        recipe_id: UUID,
        db: Session
    ) -> List[float]:
        """
        Generate vector embedding for a recipe
        
        Uses OpenAI text-embedding-3-small model
        Combines: title, description, ingredients, tags
        """
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        
        if not recipe:
            return None
        
        # Combine recipe text for embedding
        text_parts = [
            recipe.title,
            recipe.description or "",
        ]
        
        # Add ingredient names
        if recipe.ingredients:
            ingredient_names = [ing.name for ing in recipe.ingredients]
            text_parts.append(" ".join(ingredient_names))
        
        # Add tags
        if recipe.tags:
            tag_names = [tag.tag for tag in recipe.tags]
            text_parts.append(" ".join(tag_names))
        
        # Add dietary info
        text_parts.append(f"dietary type: {recipe.dietary_type}")
        
        if recipe.is_diabetic_friendly:
            text_parts.append("diabetic friendly")
        if recipe.is_heart_healthy:
            text_parts.append("heart healthy")
        if recipe.is_gluten_free:
            text_parts.append("gluten free")
        if recipe.is_dairy_free:
            text_parts.append("dairy free")
        
        combined_text = " ".join(text_parts)
        
        # TODO: Generate embedding using OpenAI
        # embedding = await openai_client.embeddings.create(
        #     model="text-embedding-3-small",
        #     input=combined_text,
        #     dimensions=1536
        # )
        # return embedding.data[0].embedding
        
        # Mock embedding (1536 dimensions)
        return [0.0] * 1536
    
    @staticmethod
    async def generate_query_embedding(
        query_text: str
    ) -> List[float]:
        """Generate embedding for search query"""
        
        # TODO: Generate embedding using OpenAI
        # embedding = await openai_client.embeddings.create(
        #     model="text-embedding-3-small",
        #     input=query_text,
        #     dimensions=1536
        # )
        # return embedding.data[0].embedding
        
        # Mock embedding
        return [0.0] * 1536
    
    @staticmethod
    async def semantic_search(
        query_embedding: List[float],
        db: Session,
        limit: int = 20,
        filters: Optional[Dict] = None
    ) -> List[Recipe]:
        """
        Perform semantic search using vector similarity
        
        Uses pgvector cosine distance for similarity
        """
        # TODO: Implement vector search with pgvector
        # query = db.query(Recipe).filter(Recipe.is_active == True)
        
        # Apply filters if provided
        # if filters:
        #     if "dietary_type" in filters:
        #         query = query.filter(Recipe.dietary_type == filters["dietary_type"])
        #     if "max_calories" in filters:
        #         query = query.filter(Recipe.calories <= filters["max_calories"])
        
        # Order by vector similarity
        # recipes = query.order_by(
        #     Recipe.embedding.cosine_distance(query_embedding)
        # ).limit(limit).all()
        
        # Fallback to simple query
        recipes = db.query(Recipe).filter(
            Recipe.is_active == True
        ).limit(limit).all()
        
        return recipes
    
    @staticmethod
    async def find_similar_recipes(
        recipe_id: UUID,
        db: Session,
        limit: int = 10
    ) -> List[Recipe]:
        """Find similar recipes based on vector similarity"""
        
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        
        if not recipe or not recipe.embedding:
            return []
        
        # TODO: Find similar using vector distance
        # similar = db.query(Recipe).filter(
        #     Recipe.id != recipe_id,
        #     Recipe.is_active == True
        # ).order_by(
        #     Recipe.embedding.cosine_distance(recipe.embedding)
        # ).limit(limit).all()
        
        # Fallback: similar dietary type and calories
        similar = db.query(Recipe).filter(
            Recipe.id != recipe_id,
            Recipe.is_active == True,
            Recipe.dietary_type == recipe.dietary_type,
            Recipe.calories.between(recipe.calories * 0.8, recipe.calories * 1.2)
        ).limit(limit).all()
        
        return similar
    
    @staticmethod
    async def batch_generate_embeddings(
        db: Session,
        batch_size: int = 100
    ):
        """
        Generate embeddings for recipes that don't have them
        
        Run as background job
        """
        recipes_without_embeddings = db.query(Recipe).filter(
            Recipe.is_active == True,
            Recipe.embedding == None
        ).limit(batch_size).all()
        
        for recipe in recipes_without_embeddings:
            embedding = await VectorSearchService.generate_recipe_embedding(
                recipe.id, db
            )
            
            if embedding:
                recipe.embedding = embedding
        
        db.commit()
        
        return len(recipes_without_embeddings)
    
    @staticmethod
    async def rag_search(
        query: str,
        user_context: Optional[Dict],
        db: Session,
        limit: int = 10
    ) -> Dict:
        """
        Retrieval Augmented Generation (RAG) search
        
        Combines:
        1. Semantic vector search
        2. User health context filtering
        3. GPT-4 for personalized recommendations
        """
        
        # Generate query embedding
        query_embedding = await VectorSearchService.generate_query_embedding(query)
        
        # Build filters from user context
        filters = {}
        if user_context:
            if "dietary_restrictions" in user_context:
                filters["dietary_restrictions"] = user_context["dietary_restrictions"]
            if "max_calories" in user_context:
                filters["max_calories"] = user_context["max_calories"]
            if "health_conditions" in user_context:
                filters["health_conditions"] = user_context["health_conditions"]
        
        # Perform semantic search
        recipes = await VectorSearchService.semantic_search(
            query_embedding,
            db,
            limit=limit * 2,  # Get more for reranking
            filters=filters
        )
        
        # TODO: Use GPT-4 to rerank and explain recommendations
        # context = [recipe.to_dict() for recipe in recipes[:20]]
        # gpt4_response = await openai_client.chat.completions.create(
        #     model="gpt-4-turbo-preview",
        #     messages=[
        #         {"role": "system", "content": "You are a nutrition expert..."},
        #         {"role": "user", "content": f"Query: {query}\nUser context: {user_context}\nRecipes: {context}"}
        #     ]
        # )
        
        return {
            "query": query,
            "results": recipes[:limit],
            "total_found": len(recipes),
            "filters_applied": filters,
            # "ai_explanation": gpt4_response.choices[0].message.content
        }
