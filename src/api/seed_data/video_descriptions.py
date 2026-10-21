"""
Long "About This Form" descriptions for the video library, keyed by video slug.

To add a description: add a new entry below (slug: text), then run
    flask seed-video-descriptions
Write plain text (each line becomes a paragraph) or the same HTML the Studio editor saves (see
src/api/rich_text.py for what is allowed). Either way it is cleaned before it is shown.
Running the command again is safe: it only updates videos that already exist.
"""

VIDEO_LONG_DESCRIPTIONS = {
    "chens-11": """<h2>What the 11 techniques are</h2>
<p>The 11 techniques Tai Chi Chuan is not one of the abbreviated Tai Chi Chuan solo forms people choreographed to teach the novice students. Rather, it is a collection of 11 essential Tai Chi Chuan techniques done separately and individually, not connected as a single sequence. It is the result of Chen Wei Ming's (1881-1958) creation based on his knowledge and experience.</p>
<h2>Who was Chen Wei Ming?</h2>
<p>The Confucian scholar <strong>Chen Wei Ming</strong> was interested in martial art since he was a boy. However, he did not engage in training until he was in his 30's. He spent two years with Sun Lu Tang (1859-1933) to study Xingyi and Bagua and eight years in Tai Chi Chuan with Yang Cheng Fu (1889-1936) and with his brother Yang Shao Hou (1862-1930). With Yang Cheng Fu's permission, he introduced this 11 techniques Tai Chi Chuan in his book published in 1929.</p>
<h2>Why practice one technique at a time</h2>
<p>He wrote in his book that Tai Chi Chuan has many benefits and should be made available to the general public. However, since the Tai Chi Chuan movements adhere to the human anatomy, they are done in circular motions and all the movements are connected together in one single sequence called a form. With this unique feature, it is difficult for beginning students to learn and remember, and difficult to promulgate to the general public.</p>
<p>Traditionally, Tai Chi Chuan teaching is based on a one-on-one, in-person setting. In each lesson, one or two movements are offered to keep up the high standard. A new movement is not offered until one has mastered the old movement. When one has completed all the movements, one has learned and mastered the form. Therefore, the quality is kept to a very high standard. This method of teaching requires a lot of time and patience from both the teacher and student. For this reason, Tai Chi Chuan practice and transmission happened in small groups of dedicated practitioners for a long time.</p>
<p>In order to promulgate Tai Chi Chuan to the general public, this traditional method of teaching needed to change, yet the quality had to stay intact. Chen Wei Ming's 11 techniques Tai Chi Chuan is the solution. It is a collection of 11 essential Tai Chi Chuan movements done individually, without any connection to other movements as one commonly witnesses today. With this 11 techniques Tai Chi Chuan available, it is easier for the novice student to learn, remember and practice. In addition, it creates interest among novice students, and the quality of each movement remains intact through individual technical practice.</p>
<p>Chen Wei Ming wrote that this individual technical practice is similar to the Ba Duan Jin (8 Pieces of Brocade) practice. After all, he wrote that in ancient times, this was how people practiced Tai Chi Chuan, one movement at a time. He speculated it was Wang Tsung Yueh (1525-1606), the author of the Tai Chi Chuan Treatise, who connected all the movements together to formalize the sequential form commonly seen today.</p>""",
}
