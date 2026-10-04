CHAPTER ?= chapters/embeddings.qmd

.PHONY: pdf count

pdf:
	scripts/render_chapter_pdf.sh $(CHAPTER) --to typst

count:
	scripts/wordcount.sh $(CHAPTER)

serve_chapter:
	quarto preview $(CHAPTER)