"""Thuật ngữ và diễn giải tiếng Việt cho báo cáo P3, không thay nhãn dữ liệu."""

COLUMNS = {
    'rating': 'Số sao', 'reviews': 'Số bài đánh giá', 'products': 'Số sản phẩm',
    'mean_words': 'Số từ trung bình', 'median_words': 'Trung vị số từ',
    'mean_helpful': 'Lượt hữu ích trung bình', 'median_helpful': 'Trung vị lượt hữu ích',
    'review_share': 'Tỷ lệ bài đánh giá', 'sentiment': 'Nhãn cảm xúc suy từ số sao',
    'mean_rating': 'Số sao trung bình', 'helpful_mean': 'Lượt hữu ích trung bình',
    'helpful_median': 'Trung vị lượt hữu ích', 'helpful_nonzero_share': 'Tỷ lệ có lượt hữu ích',
    'verified_share': 'Tỷ lệ mua hàng đã xác minh',
    'negative_count': 'Số bài tiêu cực', 'negative_share': 'Tỷ lệ tiêu cực',
    'neutral_count': 'Số bài trung tính', 'neutral_share': 'Tỷ lệ trung tính',
    'positive_count': 'Số bài tích cực', 'positive_share': 'Tỷ lệ tích cực',
    'negative_ci_low': 'Cận dưới khoảng tin cậy tỷ lệ tiêu cực',
    'negative_ci_high': 'Cận trên khoảng tin cậy tỷ lệ tiêu cực',
    'sufficient_support': 'Đạt ngưỡng số mẫu để trình bày',
    'level_1': 'Đơn vị đo độ dài', 'count': 'Số mẫu', 'mean': 'Trung bình',
    'std': 'Độ lệch chuẩn', 'min': 'Nhỏ nhất', '25%': 'Phân vị 25%',
    '50%': 'Trung vị (phân vị 50%)', '75%': 'Phân vị 75%', 'max': 'Lớn nhất',
    'bin': 'Khoảng độ dài theo số từ', 'field': 'Trường dữ liệu',
    'missing': 'Số giá trị thiếu', 'empty_strings': 'Số chuỗi rỗng', 'rows': 'Số hàng',
    'n': 'Số từ trong cụm', 'term': 'Từ hoặc cụm từ nguyên bản',
    'documents': 'Số bài chứa từ/cụm từ', 'share': 'Tỷ lệ bài có từ/cụm từ',
    'class_documents': 'Tổng số bài trong lớp', 'total_documents': 'Tổng số bài chứa từ/cụm từ ở mọi lớp',
    'prevalence': 'Tỷ lệ xuất hiện trong lớp', 'rest_prevalence': 'Tỷ lệ xuất hiện ngoài lớp',
    'prevalence_difference': 'Chênh lệch trong lớp trừ ngoài lớp (điểm %)',
    'smoothed_lift': 'Tỷ số mức phổ biến đã làm trơn',
    'brand_normalized': 'Thương hiệu đã chuẩn hóa', 'parent_asin': 'Mã sản phẩm cha Amazon',
    'month': 'Tháng', 'year': 'Năm', 'verified_purchase': 'Giao dịch mua đã xác minh',
    'theme': 'Chủ đề từ điển', 'mention_reviews': 'Số bài trong lớp nhắc chủ đề',
    'class_reviews': 'Tổng số bài trong lớp', 'within_class_share': 'Tỷ lệ nhắc chủ đề trong lớp',
    'overall_mentions': 'Số bài nhắc chủ đề ở mọi lớp', 'overall_share': 'Tỷ lệ nhắc chủ đề trên toàn bộ dữ liệu',
    'proxy_label': 'Nhãn đại diện suy từ số sao', 'review_id': 'Mã bài đánh giá',
    'snippet': 'Trích đoạn tiếng Anh nguyên bản', 'status': 'Trạng thái sử dụng',
    'noise_candidate_reasons': 'Lý do đưa vào nhóm nghi nhiễu',
    'text': 'Nội dung tiếng Anh nguyên bản', 'annotation_status': 'Trạng thái gán nhãn',
    'source': 'Nguồn dữ liệu', 'source_line': 'Dòng trong tệp nguồn',
    'group': 'Nhóm sản phẩm', 'asin': 'Mã biến thể sản phẩm Amazon',
    'user_id': 'Mã người dùng', 'review_title': 'Tiêu đề bài đánh giá',
    'product_title': 'Tiêu đề sản phẩm', 'brand': 'Thương hiệu',
    'timestamp': 'Dấu thời gian', 'helpful_vote': 'Lượt đánh dấu hữu ích',
    'raw_text': 'Văn bản trước làm sạch', 'brand_raw': 'Thương hiệu trước chuẩn hóa',
    'label_id': 'Mã số nhãn cảm xúc', 'label_provenance': 'Nguồn gốc nhãn',
    'quality_flags': 'Cờ kiểm tra chất lượng', 'clean_text_sha256': 'Hàm băm văn bản đã làm sạch',
    'language': 'Ngôn ngữ', 'language_detector_score': 'Điểm bộ nhận diện ngôn ngữ',
    'near_duplicate_group_id': 'Mã nhóm văn bản gần trùng',
}

VALUES = {
    'negative': 'tiêu cực', 'neutral': 'trung tính', 'positive': 'tích cực',
    'True': 'có/đúng', 'False': 'không/sai',
    'battery': 'pin', 'build': 'kết cấu', 'display': 'màn hình', 'keyboard': 'bàn phím',
    'performance': 'hiệu năng', 'portability': 'tính di động', 'price': 'giá',
    'storage': 'lưu trữ', 'thermals_noise': 'nhiệt độ/tiếng ồn',
    'character_count': 'số ký tự', 'word_count': 'số từ tách bằng khoảng trắng',
    'regex_token_count': 'số đơn vị từ tách bằng biểu thức chính quy',
    'LEXICAL_CONTEXT_NOT_ASPECT_SENTIMENT': 'ngữ cảnh từ vựng, chưa phải nhãn cảm xúc khía cạnh',
    'UNANNOTATED_DIAGNOSTIC_NOT_GOLD': 'mẫu chẩn đoán chưa gán nhãn, không phải bộ kiểm thử chuẩn thủ công',
    'UNKNOWN': 'chưa xác định', 'AMBIGUOUS': 'mơ hồ',
    'five_star_negative_or_mixed_cue': '5 sao nhưng có dấu hiệu tiêu cực hoặc khen chê đan xen',
}

TERMS = {
    'not': 'không; từ phủ định', 'no': 'không', 'great': 'rất tốt', 'good': 'tốt',
    'screen': 'màn hình', 'use': 'sử dụng', 'all': 'tất cả', 'one': 'một',
    'up': 'lên; nghĩa tùy ngữ cảnh', 'just': 'chỉ/vừa', 'like': 'thích/giống như',
    'only': 'chỉ', 'when': 'khi', "it's": 'nó là; dạng viết tắt', 'get': 'nhận/đạt được',
    'battery': 'pin', 'price': 'giá', 'about': 'về/khoảng', 'out': 'ra/ngoài',
    'after': 'sau', 'work': 'hoạt động/làm việc', 'keyboard': 'bàn phím',
    'bought': 'đã mua', 'what': 'điều gì', 'time': 'thời gian',
    'do not': 'không', 'would not': 'đã không/không chịu', 'it back': 'nó trở lại; thường đi với gửi trả',
    'to return': 'để trả lại', 'stopped working': 'đã ngừng hoạt động',
    'not buy': 'không mua', 'will not': 'sẽ không', 'a year': 'một năm',
    'return it': 'trả lại sản phẩm', 'not work': 'không hoạt động',
    'is not': 'không phải/không', 'the battery': 'pin', 'a good': 'một … tốt; cụm chưa hoàn chỉnh',
    'the keyboard': 'bàn phím', 'to get': 'để có được', 'does not': 'không',
    'when i': 'khi tôi', 'i guess': 'tôi đoán/tôi nghĩ', 'the screen': 'màn hình',
    "i don't": 'tôi không', 'so far': 'cho đến hiện tại', 'i love': 'tôi rất thích',
    'a great': 'một … rất tốt; cụm chưa hoàn chỉnh', 'battery life': 'thời lượng pin',
    'the price': 'giá', 'easy to': 'dễ để …', 'love it': 'rất thích sản phẩm',
    'the best': 'tốt nhất', 'happy with': 'hài lòng với', 'fast and': 'nhanh và …',
    'slow': 'chậm', 'fast': 'nhanh', 'memory': 'bộ nhớ', 'hard drive': 'ổ lưu trữ',
    'quality': 'chất lượng', 'computer': 'máy tính', 'laptop': 'máy tính xách tay',
    'excellent': 'xuất sắc', 'perfect': 'hoàn hảo', 'bad': 'tệ', 'problem': 'vấn đề',
    'problems': 'các vấn đề', 'works': 'hoạt động', 'easy': 'dễ', 'cheap': 'rẻ',
    'value': 'giá trị', 'speed': 'tốc độ', 'windows': 'Windows; hệ điều hành',
}

GLOSSARY = [
    ('EDA', 'phân tích khám phá dữ liệu: mô tả phân bố, quan hệ và các điểm cần kiểm tra'),
    ('review', 'bài đánh giá của người dùng'), ('insight', 'nhận định rút ra từ dữ liệu'),
    ('proxy label', 'nhãn đại diện, ở đây suy từ số sao; không phải nhãn con người gán'),
    ('metadata', 'siêu dữ liệu mô tả sản phẩm hoặc giao dịch'),
    ('median', 'trung vị: giá trị ở giữa khi sắp xếp; khác trung bình cộng'),
    ('percentile / quantile', 'phân vị: mốc chia dữ liệu theo tỷ lệ; p90 là mốc 90% số mẫu không vượt quá'),
    ('n-gram', 'chuỗi n từ liên tiếp; unigram là một từ, bigram là hai từ, trigram là ba từ'),
    ('document frequency', 'số bài có từ/cụm từ, mỗi bài chỉ được đếm một lần'),
    ('prevalence', 'tỷ lệ xuất hiện trong nhóm đang xét'),
    ('smoothed lift', 'tỷ số mức phổ biến trong lớp so với phần còn lại, có làm trơn để tránh tỷ số cực đoan'),
    ('support', 'số mẫu hỗ trợ một thống kê; quá ít mẫu thì tỷ lệ thiếu ổn định'),
    ('confidence interval / CI', 'khoảng tin cậy của ước lượng theo các giả định thống kê; không phải độ tin cậy dự đoán của mô hình'),
    ('percentage point / pp', 'điểm phần trăm: 36,58% trừ 26,28% bằng 10,30 điểm phần trăm'),
    ('Spearman', 'hệ số tương quan thứ hạng; có liên hệ không đồng nghĩa có quan hệ nhân quả'),
    ('ABSA', 'phân tích cảm xúc theo khía cạnh, như pin, màn hình hoặc bàn phím'),
    ('ATE / ASC', 'trích xuất cụm từ khía cạnh / phân loại cảm xúc theo khía cạnh'),
    ('gold test', 'bộ kiểm thử chuẩn do con người gán nhãn độc lập'),
    ('macro F1', 'trung bình F1 của từng lớp với trọng số bằng nhau, giúp chú ý cả lớp ít mẫu'),
    ('QA', 'kiểm tra chất lượng; QA lọc đúng laptop khác với gán nhãn cảm xúc chuẩn'),
    ('platform/style shift', 'khác biệt nền tảng hoặc phong cách viết giữa SemEval và Amazon trong cùng phạm vi laptop'),
]


def interpretations(tables: dict[str, list[dict[str, str]]], summary: dict) -> tuple[dict[str, str], dict[str, str]]:
    """Diễn giải thống kê từ bảng đã lưu; không tạo nhãn hoặc đánh giá mô hình."""
    n = summary['rows']
    def integer(value: float) -> str:
        return f'{int(value):,}'.replace(',', '.')
    def percent(value: float) -> str:
        return f'{value * 100:.2f}'.replace('.', ',') + '%'
    labels = {r['sentiment']: r for r in tables['sentiment']}
    counts = {k: int(v['reviews']) for k, v in labels.items()}
    rating = {r['rating']: r for r in tables['rating']}
    product_rows = tables['products']
    sparse = sum(int(r['reviews']) == 1 for r in product_rows)
    supported = sum(int(r['reviews']) >= 30 for r in product_rows)
    brands = sorted(tables['brands'], key=lambda r: int(r['reviews']), reverse=True)
    top5 = sum(int(r['reviews']) for r in brands[:5]) / n
    years = {r['year']: r for r in tables['years']}
    verified = {r['verified_purchase']: r for r in tables['verified']}
    missing = {r['field']: r for r in tables['missing']}
    most_bin = max(tables['length_histogram'], key=lambda r: int(r['reviews']))
    not_row = next(r for r in tables['frequent_terms'] if r['n'] == '1' and r['term'] == 'not')
    themes = {r['theme']: r for r in tables['themes']}
    top_themes = sorted(themes.values(), key=lambda r: int(r['overall_mentions']), reverse=True)[:3]
    theme_names = ', '.join(f"{VALUES[r['theme']]} {percent(float(r['overall_share']))}" for r in top_themes)
    table_notes = {
        'rating': f"Nhóm 5 sao có {integer(int(rating['5']['reviews']))} bài ({percent(float(rating['5']['review_share']))}), lớn nhất trong dữ liệu. Trung vị nhóm 2 sao là {rating['2']['median_words']} từ, cao hơn nhóm 5 sao ({rating['5']['median_words']} từ); lời chê có thể cần diễn giải dài hơn, nhưng số sao không chứng minh cảm xúc thật.",
        'sentiment': f"Nhãn tích cực chiếm {percent(counts['positive']/n)}, trong khi trung tính chỉ {percent(counts['neutral']/n)}. Đây là mất cân bằng lớp; khi so mô hình cần xem macro F1 (F1 trung bình đều giữa các lớp) và kết quả từng lớp, không chỉ accuracy (tỷ lệ dự đoán đúng chung).",
        'length_by_sentiment': f"Trung vị độ dài của nhóm tiêu cực/trung tính/tích cực lần lượt là {labels['negative']['median_words']}/{labels['neutral']['median_words']}/{labels['positive']['median_words']} từ. Nhóm tích cực ngắn hơn trong mẫu này; cần phân biệt số ký tự, số từ và số token (đơn vị tách văn bản), không coi chúng là cùng một thước đo.",
        'length_histogram': f"Khoảng {most_bin['bin']} từ chứa nhiều bài nhất: {integer(int(most_bin['reviews']))} bài ({percent(int(most_bin['reviews'])/n)}). Có {integer(summary['short_under_5_words'])} bài dưới 5 từ ({percent(summary['short_under_5_words']/n)}); trung vị toàn bộ là {summary['median_words']:g} từ, còn p90 (phân vị 90%) là {summary['p90_words']:g} từ, cho thấy đuôi dài.",
        'missing': f"Các trường bắt buộc như mã bài, văn bản và số sao không thiếu trong bộ cuối. Trường thương hiệu thiếu {missing['brand']['missing']} giá trị; brand_raw (thương hiệu gốc) có {missing['brand_raw']['empty_strings']} chuỗi rỗng. near_duplicate_group_id (mã nhóm gần trùng) thiếu cả {integer(int(missing['near_duplicate_group_id']['missing']))} hàng vì chưa được gán nhóm, không phải bằng chứng siêu dữ liệu nối sai.",
        'frequent_terms': f"Từ not (không; phủ định) có trong {integer(int(not_row['documents']))} bài ({percent(float(not_row['share']))}). Điều này củng cố việc giữ phủ định khi tiền xử lý. Số bài chứa từ không phải số lần từ lặp lại, và tần suất từ không xác định cảm xúc khía cạnh.",
        'lexical_by_class': "Cụm stopped working (đã ngừng hoạt động) xuất hiện ở 4,81% bài tiêu cực nhưng 0,42% bài ngoài lớp; battery life (thời lượng pin) có ở 11,03% bài tích cực và 4,34% phần còn lại. Các cụm này giúp đặt giả thuyết về lỗi vận hành và pin; nhắc đến pin trong bài tích cực chưa chứng minh người viết khen pin.",
        'brands': f"Năm nhóm thương hiệu {', '.join(r['brand_normalized'] for r in brands[:5])} chiếm {percent(top5)} số bài. Dữ liệu tập trung vào vài nhóm; các nhóm ít mẫu khó so sánh ổn định. Đây là nhóm từ siêu dữ liệu, không phải thị phần, xếp hạng chất lượng hãng hoặc bằng chứng nhà sản xuất đã được xác minh.",
        'products': f"Có {integer(sparse)}/{integer(len(product_rows))} sản phẩm chỉ có một bài, còn {supported} sản phẩm đạt ít nhất 30 bài. Vì vậy tỷ lệ tiêu cực ở sản phẩm rất ít mẫu dễ dao động; không nên xếp hạng toàn bộ sản phẩm bằng một tỷ lệ đơn lẻ. Khoảng tin cậy trong bảng dựa trên giả định thống kê, không phải điểm tin cậy của mô hình.",
        'months': f"Có {len(tables['months'])} tháng có bài đánh giá, trong khoảng từ {summary['time_min'][:10]} đến {summary['time_max'][:10]}. Số bài thay đổi theo thời gian phản ánh mẫu được chọn; không thể coi là doanh số. Chỉ diễn giải tỷ lệ ở nhóm đủ mẫu; đầu/cuối giai đoạn và năm 2023 là dữ liệu một phần.",
        'years': f"Tỷ lệ tiêu cực năm 2014 là {percent(float(years['2014']['negative_share']))}, năm 2022 là {percent(float(years['2022']['negative_share']))}, năm 2023 là {percent(float(years['2023']['negative_share']))}. Đây là chênh lệch thành phần mẫu theo năm, không đủ kết luận chất lượng laptop giảm vì sản phẩm, thương hiệu, tuổi bài và cách lấy mẫu cùng thay đổi.",
        'verified': f"Giao dịch mua đã xác minh có {integer(int(verified['True']['reviews']))} bài ({percent(int(verified['True']['reviews'])/n)}). Tỷ lệ tiêu cực là {percent(float(verified['True']['negative_share']))}, thấp hơn nhóm chưa xác minh ({percent(float(verified['False']['negative_share']))}); trung vị độ dài tương ứng {verified['True']['median_words']} và {verified['False']['median_words']} từ. Đây là liên hệ mô tả, không chứng minh nhóm chưa xác minh là đánh giá giả.",
        'themes': f"Ba chủ đề được nhắc nhiều nhất theo từ điển là {theme_names}. Một bài có thể nhắc nhiều chủ đề nên các tỷ lệ không cộng thành 100%; nhãn cảm xúc của cả bài không phải cảm xúc của từng chủ đề.",
        'theme_contexts': f"{len(tables['theme_contexts'])} trích đoạn giúp đọc ngữ cảnh của {len(themes)} chủ đề. Có bài tích cực vẫn chê thời lượng pin hoặc so sánh với máy cũ, cho thấy cần tách cảm xúc tổng thể và cảm xúc khía cạnh. Đây là ví dụ được chọn để chẩn đoán, không phải mẫu đại diện để ước lượng tỷ lệ khiếu nại hay nhãn chuẩn thủ công.",
        'noise_examples': f"{len(tables['noise_examples'])} ví dụ này lấy từ 250 mẫu nghi nhiễu được dành riêng, ngoài bộ cuối {integer(n)} bài. Một bài 5 sao vẫn có thể vừa khen vừa chê; dấu hiệu tiêu cực không tự chứng minh số sao sai. Không tự đổi nhãn hoặc suy tỷ lệ nhiễu thực từ nhóm được chọn có chủ đích này.",
    }
    figure_notes = {
        'rating_proxy': f"Nhóm 5 sao lớn nhất ({percent(float(rating['5']['review_share']))}); sau ánh xạ số sao, lớp tích cực chiếm {percent(counts['positive']/n)}, còn trung tính chỉ {percent(counts['neutral']/n)}. Mất cân bằng này là lý do cần xem kết quả từng lớp và macro F1 (F1 trung bình đều giữa các lớp). Các nhãn vẫn là đại diện suy từ số sao, chưa phải cảm xúc chuẩn do con người gán.",
        'length': f"Trung vị toàn bộ là {summary['median_words']:g} từ nhưng p90 (phân vị 90%) lên tới {summary['p90_words']:g} từ, cho thấy có nhóm bài dài. Trung vị nhóm tiêu cực/trung tính/tích cực lần lượt {labels['negative']['median_words']}/{labels['neutral']['median_words']}/{labels['positive']['median_words']} từ. Vì độ dài khác nhau giữa các lớp, cần thận trọng khi so tần suất từ hoặc chọn giới hạn độ dài văn bản.",
        'distinctive_bigrams': table_notes['lexical_by_class'] + ' Trục ngang là chênh lệch điểm phần trăm, không phải mức cảm xúc của từ.',
        'brands': table_notes['brands'],
        'time': f"Số bài theo tháng không đều; biểu đồ chỉ trình bày tỷ lệ ở nhóm có ít nhất 100 bài. Tỷ lệ tiêu cực theo năm tăng từ {percent(float(years['2014']['negative_share']))} năm 2014 lên {percent(float(years['2022']['negative_share']))} năm 2022, nhưng chưa kiểm soát khác biệt sản phẩm và lấy mẫu. Không suy doanh số hoặc kết luận chất lượng laptop giảm từ đồ thị này.",
        'verified_purchase': table_notes['verified'], 'themes': table_notes['themes'],
    }
    return table_notes, figure_notes
