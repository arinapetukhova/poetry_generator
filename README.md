# RAPTOR RAG based AI-Lyrics Generator 
ATLLM project, fall 2025

The project explores using RAPTOR RAG approach in making an AI-Lyrics Generator. Data for RAG was scrapped from [genius.com](https://genius.com) and included 83 musicians of 5 genres (pop, rock, soul, rap, alternative). Each musician had 25 scrapped songs, therefore, 2075 songs in total were added into the dataset. Moreover, for genre and musician hierarchy levels metadata aboout genres and musisians was generated with LLM. Based on the dataset, modular RAPTOR RAG system was implemented with ChromaDB (hierarchy of the system is Genre -> Musician -> Song). Then, this RAG system was integrated in the AI-Lyrics Generator and deployed on [render.com](https://render.com).
