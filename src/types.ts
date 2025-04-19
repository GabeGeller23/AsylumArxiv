export interface Paper {
  title: string;
  authors: string | string[];
  first_author: string;
  summary: string;
  published: string;
  link: string;
  summary_bullets: string;
  tags: string;
  relevance_score: number;
  h_index: number;
  affiliation: string;
  citations: number;
  author_url: string;
  linkedin_search: string;
  total_score: number;
}

export interface AuthorInfo {
  name: string;
  h_index: number;
  affiliation: string;
  paper_count: number;
  citations: number;
  profile_url: string;
  linkedin_url: string;
} 