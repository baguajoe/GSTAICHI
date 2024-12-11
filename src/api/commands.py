
import click
from api.models import db, User, Article
from datetime import datetime


"""
In this file, you can add as many commands as you want using the @app.cli.command decorator
Flask commands are usefull to run cronjobs or tasks outside of the API but sill in integration 
with youy database, for example: Import the price of bitcoin every night as 12am
"""
def setup_commands(app):
    
    """ 
    This is an example command "insert-test-users" that you can run from the command line
    by typing: $ flask insert-test-users 5
    Note: 5 is the number of users to add
    """
    @app.cli.command("insert-test-users") # name of our command
    @click.argument("count") # argument of out command
    def insert_test_users(count):
        print("Creating test users")
        for x in range(1, int(count) + 1):
            user = User()
            user.email = "test_user" + str(x) + "@test.com"
            user.password = "123456"
            user.is_active = True
            db.session.add(user)
            db.session.commit()
            print("User: ", user.email, " created.")

        print("All test users created")

    @app.cli.command("seed-articles")
    def seed_articles():
        print("Creating article...")
        
        part_one = """
Combat Tai Chi Chuan

The martial art of Tai Chi Chuan follows Tai Chi philosophy. Everything that relates to Tai Chi Chuan has Yin and Yang components -- from the philosophy, the physical movement, the training to the functions of the art.

Many people practice Tai Chi Chuan today as a health exercise but it is as well a very effective internal martial art. Tai Chi Chuan, with its soft and slow movements, may be difficult to accept as a fighting system for some people, but that's what it is, that's what it has been for many generations.

In traditional martial art training, the emphasis of Tai Chi Chuan is more on the preparation and development of internal power than the individual technique as in most external martial art styles. There is hardly training in specific applications. This is why it is difficult for a beginner to understand and see the technical skill in Tai Chi Chuan. Unless one is trained under a knowledgeable teacher, a practitioner can spend decade or more and still not be sure how to correctly apply each movement in fighting.

A philosophy of Tai Chi Chuan combat is that if you say there is technique, there is none. If you say that there is not, the technique is everywhere. This is like the water supporting the boat: the boat is always on top of the water although the boat has done nothing. In martial art training, it is essential for the practitioner to prepare his or her physical condition for combat. In Tai Chi Chuan, the practitioner does not rehearse for the combat itself which is an unpredictable situation. The training is not focused on the application of each individual movement but on developing oneself totally so that the body becomes nimble and flexible, the feet mobile, the hands are fast, and there is correct timing in execution. These are the essential ingredients in combat.

With a unique training style, we practice Tai Chi Chuan's Solo Form with the following three principles in mind:

1. Softness Controls Hardness
The reason Tai Chi Chuan favors soft over hard is partly based on the principle of soft overcoming hard as described by Lao Tzu's "Tao Te Ching". The other reason is to prevent the practitioner from performing a head-on collision with the opponent.
The belief that in combat hard and powerful are always victorious is a fallacy. It is common in confrontation that both parties apply and mobilize power to try to overcome each other: The winner is usually the stronger. In some cases, both protagonists lose when both have equal power and skill. Tai Chi Chuan's emphasis on the principle of soft overcoming hard tries to avoid this situation.
There is a belief that the principle of softness overcoming hardness means avoidance. This is not true, because nobody who is on the defensive all the time comes out victorious. Tai Chi Chuan's emphasis on soft and hard interaction is based on soft as in yielding or deflection and hard as in attacking, and the two components always go together.

a. Yielding and striking at the same time
Tai Chi Chuan's emphasis on the technique of yielding and attacking at the same time means there should be defensive and offensive intention in each movement so that the counterstrike will be quicker and will seize the opponent's weak area before he can recover. This combination involves every part of the body; thus one must train the whole body to be sensitive, nimble and flexible. This is different from most martial arts styles where offensive and defensive techniques occur separately.

b. Combination strikes
To be able to strike continuously is something all practitioners would like to do. This does not give the opponent a chance to rest and recover. In many styles of martial arts, combination strikes are generally pre-arranged exercises to improve one's physical endurance and confrontation experiences. In Tai Chi Chuan training, one sees this combination as one circle. Half the circle is for offense and half for defense. The Tai Chi Chuan Classics refer to this as "The retreating circle is easy but the advancing circle is difficult."

How to execute the circle completely in a combat situation? It is believed that one should "give up oneself" - meaning a state of egolessness -- and follow the opponent. To be able to follow the opponent, one has to be able to stick to the opponent's movement. This means one is sticking to the opponent whenever there is a chance to be in contact with the opponent's body. Sticking to the opponent does not mean simply to stick to the opponent but to get a superior position as the result of this execution. What is the skill to get us to this superior position? How quickly do you respond? What is the correct amount of power? Which part of the body to stick? These are the experiences one will gain from practice.

Following the opponent's technique involves the whole body. Its movements will result in the practitioner gaining a superior position based on the opponent's strike and combat situation. Generally, it requires the feet to move in coordination with the upper body. When one is able to do this, no matter what the situation, one is able to maintain balance and find the opportunity to be on the superior position to strike. The superior position is defined as one in an active role over the opponent's passive role. Inferior position is when one is in a passive role and the situation is controlled by the opponent. Based on the information obtained from applying the stick and follow techniques, one can mobilize the body to counter the opponent's strike. Therefore, this is one of the reasons why a Tai Chi Chuan practitioner is able to move so fast or has such a quick reflex. In Push Hand exercises, we train the skills of listening, forgetting oneself and following the opponent, etc. It is not a competition sport as promoted in today's tournament.

c. No empty strike
With its emphasis on Yin and Yang balance, Tai Chi Chuan's movements are soft, relaxed and circular. This means that all movements have both the soft component power and the hard component power. The dynamics shift to either side based on the opponent's strike. When the opponent strikes, the soft component makes the opponent lose balance and the hard component strikes back. When the movement is circular, it does not overextend; thus, the body is balanced and is able to issue power to strike or to get a superior position. This is why in Solo Form practice, all the movements are circular. When one is balanced, one is able to move the feet to get a superior position and to avoid falling into an inferior position.
"""

        part_two = """
2. Tranquility Controls Action
Although the principle of soft component for yielding and hard component for attacking is sound, it will only work when the practitioner has good timing and correct execution. This requires good skill, calmness, and a nimble body. If one is not calm, one is not able to let the opponent come in until the last minute. If the body is not nimble, one cannot react suddenly without hurting the body. If the skill is not good, one cannot control the opponent quickly. Tai Chi Chuan does not believe in taking the initiative but if the situation requires, one will make it happen.
The Tai Chi Chuan Classics say, "Retreating circle is easy to do, the advancing circle is difficult." Retreating circle refers to defensive movement and advancing circle refers to offensive movement. The two components always go together. Which one to use is determined by the opponent's strike. When the practitioner takes the inactive position, there are some advantages over the opponent:

The practitioner must have confidence and calm to anticipate the opponent's strike. The practitioner has the psychological advantage.
The practitioner will understand the strike and power from the opponent's. It is an advantage to find the opponent's weak areas.
The practitioner will save energy and not get tired easily. This is an advantage in physical endurance.
The opponent does not know what the practitioner will do. This has the advantage of confusing the opponent.
Invite the opponent to strike and react based on the strike. An advantage is to hide the weak area from the opponent.
When one is unselfish, this has the advantage in self-control and temperament. For one to be able to perform this principle correctly, a practitioner must be able to perform the following concepts:
A. Give up oneself and follow the opponent
It is common in the martial art community that a stronger person who can execute a technique quickly has better chance to win. When the opponent strikes, one should instinctively mobilize the power to confront and defend against the strike. This inborn reaction is possessed by everyone, but martial art practitioners often train their bodies so that the reaction or reflex will be accurate, powerful, speedy, and effective. Some practitioners even train their arms and body to develop a body armor to resist a powerful strike. Unfortunately, many practitioners physically suffer a great deal in training but the outcome is still determined by how powerful the strike and how fast one can apply the technique. This concept is centered on the practitioner himself.
Tai Chi Chuan is an outgrowth of Taoist philosophy that says everything is based on nature. In order to be natural, the concentration must shift from oneself to the opponent. In order to be able to follow, the practitioner has to give up on initiation and concern for the outcome and forget himself so that all the strikes will be based on the opponent's movements. When one gives up on oneself, it means forgetting oneself and the ego and being unselfish. When one forgets oneself and is unselfish, the temperament improves and there is no pressure. When there is no pressure, the body is relax and natural. When the body is relaxed and natural, the body is nimble, mobile and flexible. These are some of the ingredients to a powerful strike.
When one is unselfish, all the reactions will have the following five characteristics:
One is able to follow the opponent's strike, left, right, up and down, without any break. Therefore, all reactions are very quick.
There will be no head-on collision. Apply soft component to listen, yield to the opponent's strike, power and reaction. Apply hard component to strike.
One will let the opponent initiate the strike.
One will disguise the movement as weakness for the opponent to come in.
One will apply a technique only to control the opponent without injury or harm.
B. Tai Chi Chuan is a short-range combat art
When it strikes, there is often a combination of strikes that involves the whole body. Here are some of the common parts of the body to apply: head, shoulders, elbows, hands, wrist, hip, knee, foot, chest, back, buttocks. Therefore, the whole body must be trained so that it is flexible enough to mobilize any part of the body that is necessary to execute a powerful strike. The lower portion of the body must be trained to be mobile so that the feet will be able to step into a superior position to compensate for the strike.
3. Apply the insubstantial to overcome the substantial
Tai Chi Chuan often applies a small amount of power to control the opponent. This is often referred to as four ounces overcome 1000 pound: Here are two of the common techniques that practitioners often use:

A. Small amount to control the large amount
This is the work of physical science. People, like everything else, are affected by gravity. When the opponent's balance is unstable, the application of a small amount of power will cause him to fall. Tai Chi Chuan practitioners often apply this kind of technique to cause the opponent to get off-balanced. This happens by re-directing the opponent's power and counter striking in between the opponent's first and the second strike. This technique is commonly referred to as "four ounces overcome a thousand pound." This task is so easy that people considered it as an insubstantial action because the performer only applied a very small amount of power to make it happen.

B. Leverage or borrowing
This is a very common technique. Borrowing power generally comes from two sources: the opponent's strike and the ground. It has a powerful result because it is the combination of the opponent's power, the practitioner's and the power coming from the ground. One can see this as a small push by the experienced Tai Chi Chuan practitioner and the opponent bounces away as a result. A muscle contraction alone can not produce this kind of power. For this technique to work, one must practice body integration regularly in the solo Form so that the body can mobilize all the power outward in a flash.

Based on the principles and techniques described above, Tai Chi Chuan practitioners often apply the following techniques and the famous eight hand techniques as ward off, roll back, press, push, pull down, split, elbow and shoulder strikes in a combat situation.

Grappling. Grappling in Tai Chi Chuan is different from other styles. It is applied to control the opponent's power. However, this is not like joint lock or disabling or injuring someone's ligament or tendons.
Pouncing. Applying the whole body forward to destroy the opponent's balance. When the opponent is off-balance, he will not be able to react. A powerful pouncing technique can cause the opponent to fall down and injuring himself.
Wrestling. Apply the weight directly or in leverage onto the opponent to cause imbalance and the opponent will fall down. This technique is also known as a "take down."
Striking. Apply strong and powerful body part to hit the opponent's weak area.
Shocking. Apply power to cause the opponent to move the whole body suddenly. It is so sudden that the opponent is not quick enough to react causing his own body to collapse, injuring himself internally. This is similar to a speeding car suddenly stopping, causing the passenger internal injury.
Emptying: It refers to the intentional disappearance of power. It is often applied by a skillful practitioner: When the opponent strikes, mobilize the power to confront the strike and remove the power suddenly. This will cause the opponent to be off balanced and fall forward.
Transparent. This refers to the opponent not being able to find the center of gravity. In other words, it does not matter how powerful the opponent's strike, when it comes close to the body, the power is not able to find the target. The result is that the body seems to be transparent.

In combat, Tai Chi Chuan is a very effective art. Generally, people see practitioners practice the Solo Form slowly and assume that this is how it works in combat situation. It is a fallacy. Slow practice serves two functions.
It fine tunes the body and especially the components that involve the body mechanics and motion so that when it moves, nothing will slow down the motion.
It trains the practitioner's perception. Therefore, practicing the Solo Form and Push Hands exercises correctly will prepared the practitioner better for combat physically as well as mentally.

In any internal art, the primary concentration is always on developing oneself and internal power. Developing martial technique is secondary. Therefore, after decades of developing oneself and internal power, a practitioner generally does not engage in any kind of confrontation unless it is absolutely necessary. When he does, a small movement from the dantien will result in a powerful strike. When Tai Chi Chuan practitioners in the past only controlled and push the opponent away so as not to cause any injury or fatality, it had a lot to do with their martial virtue.
Kindness does not mean weakness.
"""



        article = Article(
            title="Combat Tai Chi Chuan",
            content_part1=part_one,
            content_part2=part_two,
            author="Vincent Chu",
            publication_date=datetime.strptime("2024-01-01", "%Y-%m-%d"),
            download_url=None,
            is_downloadable=True
        )

        db.session.add(article)
        db.session.commit()
        print(f"Article '{article.title}' added successfully!")

    @app.cli.command("insert-test-data")
    def insert_test_data():
        pass

