import sys
import torch
from modeling_indictrans import IndicTransForConditionalGeneration
from IndicTransTokenizer.utils import preprocess_batch, postprocess_batch
from IndicTransTokenizer.tokenizer import IndicTransTokenizer


en_indic_ckpt_dir = sys.argv[1]
indic_en_ckpt_dir = sys.argv[2]
BATCH_SIZE = 4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


indictrans2-indic-en-1.1b

def initialize_model_and_tokenizer(ckpt_dir, direction):
    tokenizer = IndicTransTokenizer(direction=direction, device=DEVICE)
    model = IndicTransForConditionalGeneration.from_pretrained(ckpt_dir).to(DEVICE)
    model.half()
    model.eval()
    return tokenizer, model


def batch_translate(input_sentences, src_lang, tgt_lang, model, tokenizer):
    translations = []
    for i in range(0, len(input_sentences), BATCH_SIZE):
        batch = input_sentences[i:i+BATCH_SIZE]

        # Preprocess the batch and extract entity mappings
        batch, entity_map = preprocess_batch(batch, src_lang=src_lang, tgt_lang=tgt_lang)

        # Tokenize the batch and generate input encodings
        encodings = tokenizer(batch, src=True, truncation=True, padding='longest', return_tensors=True)
        input_ids, attention_mask = encodings['input_ids'], encodings['attention_mask']

        # Generate translations using the model
        generated_tokens = model.generate(
            input_ids,
            attention_mask=attention_mask,
            num_return_sequences=1,
            num_beams=5,
            max_length=256,
            min_length=0
        )

        # Decode the generated tokens into text
        generated_tokens = tokenizer.batch_decode(generated_tokens.detach().cpu().tolist(), src=False)

        # Postprocess the translations, including entity replacement
        translations += postprocess_batch(generated_tokens, lang=tgt_lang, placeholder_entity_map=entity_map)

        del input_ids, attention_mask
        torch.cuda.empty_cache()

    return translations


en_indic_tokenizer, en_indic_model = initialize_model_and_tokenizer(en_indic_ckpt_dir, "en-indic")
indic_en_tokenizer, indic_en_model = initialize_model_and_tokenizer(indic_en_ckpt_dir, "indic-en")


# ---------------------------------------------------------------------------
#                              Hindi to English
# ---------------------------------------------------------------------------
hi_sents = [
    "जब मैं छोटा था, मैं हर रोज़ पार्क जाता था।",
    "उसके पास बहुत सारी पुरानी किताबें हैं, जिन्हें उसने अपने दादा-परदादा से विरासत में पाया।",
    "मुझे समझ में नहीं आ रहा कि मैं अपनी समस्या का समाधान कैसे ढूंढूं।",
    "वह बहुत मेहनती और समझदार है, इसलिए उसे सभी अच्छे मार्क्स मिले।",
    "हमने पिछले सप्ताह एक नई फिल्म देखी जो कि बहुत प्रेरणादायक थी।",
    "अगर तुम मुझे उस समय पास मिलते, तो हम बाहर खाना खाने चलते।",
    "वह अपनी दीदी के साथ बाजार गयी थी ताकि वह नई साड़ी खरीद सके।",
    "राज ने मुझसे कहा कि वह अगले महीने अपनी नानी के घर जा रहा है।",
    "सभी बच्चे पार्टी में मज़ा कर रहे थे और खूब सारी मिठाइयाँ खा रहे थे।",    
    "मेरे मित्र ने मुझे उसके जन्मदिन की पार्टी में बुलाया है, और मैं उसे एक तोहफा दूंगा।"
]
src_lang, tgt_lang = "hin_Deva", "eng_Latn"
en_translations = batch_translate(hi_sents, src_lang, tgt_lang, indic_en_model, indic_en_tokenizer)

print(f"\n{src_lang} - {tgt_lang}")
for input_sentence, translation in zip(hi_sents, en_translations):
    print(f"{src_lang}: {input_sentence}")
    print(f"{tgt_lang}: {translation}")


# ---------------------------------------------------------------------------
#                              English to Hindi
# ---------------------------------------------------------------------------
en_sents = [
    "When I was young, I used to go to the park every day.",
    "He has many old books, which he inherited from his ancestors.",
    "I can't figure out how to solve my problem.",
    "She is very hardworking and intelligent, which is why she got all the good marks.",
    "We watched a new movie last week, which was very inspiring.",
    "If you had met me at that time, we would have gone out to eat.",
    "She went to the market with her sister to buy a new sari.",
    "Raj told me that he is going to his grandmother's house next month.",
    "All the kids were having fun at the party and were eating lots of sweets.",
    "My friend has invited me to his birthday party, and I will give him a gift."
]
src_lang, tgt_lang = "eng_Latn", "hin_Deva"
hi_translations = batch_translate(en_sents, src_lang, tgt_lang, en_indic_model, en_indic_tokenizer)

print(f"\n{src_lang} - {tgt_lang}")
for input_sentence, translation in zip(en_sents, hi_translations):
    print(f"{src_lang}: {input_sentence}")
    print(f"{tgt_lang}: {translation}")

