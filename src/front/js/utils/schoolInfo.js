// School, teacher and lineage text shared by the Gin Soon pages (Instructors, AboutUs, Lineage) and the
// Tai Chi Company app (landing page and About page). Update facts here so every page stays the same.
import vincentImage from "../../img/VincentHoldBall.jpg";
import ginSoonImage from "../../img/GinSoon2.jpg";
import gordonImage from "../../img/gordonfairlady2.png";
import tonyZhuImage from "../../img/IMG_0986.jpg";
import GSCYSC from "../../img/GSCYSC.jpg";
import GinSoonBall from "../../img/GinSoonBall.jpg";
import GinSoonSnakeCreep from "../../img/GinSoonSnakeCreep.jpg";
import GinSoonPerryPunch from "../../img/GinSoonPerryPunch.jpg";
import yeungLouSimImage from "../../img/Yeung Lou Sim.gif";
import yeungKinHouImage from "../../img/Yeung Kin Hou.gif";
import yeungBanHouImage from "../../img/Yeung Ban Hou.gif";
import yeungSiuHouImage from "../../img/Yeung Siu Hou.gif";
import yeungChingPoImage from "../../img/Yeung Ching Po.gif";
import yeungSauChungImage from "../../img/Yeung Sau Chung.jpg";
import yeungTaiYeeImage from "../../img/Yeung Tai Yee.gif";
import ipTaiTakImage from "../../img/Ip Tai Tak.gif";

export const ginSoonChu = {
    name: "Master Gin Soon Chu",
    image: ginSoonImage,
    bio: "Master Gin Soon Chu began his study of Tai Chi Chuan under Master Lai Hok Soon in Hong Kong in 1956. " +
        "Upon the passing of Master Lai in 1964, he inherited the school. Later, Master Chu became a student " +
        "of the famous Grand Master Yeung Sau Chung, the world leader of the Yang school. In 1977, he was accepted " +
        "as a disciple and was made responsible for propagating the Yang family tradition throughout North America. " +
        "Master Chu personally supervises his classes with the assistance of senior students."
};

export const vincentChu = {
    name: "Master Vincent Chu, M.Ed.",
    image: vincentImage,
    // The first two sentences of the bio, for short introductions
    shortBio: "Vincent Chu, the second son of Gin Soon Chu, is a sixth-generation lineage practitioner of the Yang Style Tai Chi Chuan. " +
        "He began assisting his father at the Gin Soon Tai Chi Chuan Club in Boston at age 16.",
    bio: "Vincent Chu, the second son of Gin Soon Chu, is a sixth-generation lineage practitioner of the Yang Style Tai Chi Chuan. " +
        "He began assisting his father at the Gin Soon Tai Chi Chuan Club in Boston at age 16. He has been teaching at the Brookline " +
        "Adult and Community Education Program since 1984. Vincent Chu has conducted many workshops and seminars in Canada and Europe " +
        "and is a frequent contributor to martial arts publications."
};

export const instructors = [
    { name: ginSoonChu.name, description: ginSoonChu.bio, image: ginSoonChu.image },
    { name: vincentChu.name, description: vincentChu.bio, image: vincentChu.image },
    {
        name: "Master Gordon Chu",
        description: "Gordon Chu is a sixth-generation lineage practitioner of Classical Yang Family Tai Chi Chuan. He is the third of three sons " +
            "of Grandmaster Gin Soon Chu. Gordon currently teaches at Gin Soon Tai Chi Club and is a co-successor of Gin Soon Tai Chi " +
            "Chuan Federation USA.",
        image: gordonImage,
    },
    {
        name: "Master Tony Zhu",
        description: "Tony Zhu is a sixth-generation Yang Style Tai Chi Chuan lineage practitioner. He was introduced to the theory and practice " +
            "of Yang Tai Chi Chuan in 1986 by his uncle, Grandmaster Gin Soon Chu. Ever since then, he has been an active Yang Style Tai Chi " +
            "practitioner. Since 1996, Tony Zhu has been an assistant instructor at the headquarters of the Gin Soon Tai Chi Chuan Federation. " +
            "In 2000, Tony Zhu travelled with Grandmaster Gin Soon Chu and his son to give seminars on Tai Chi Chuan in Europe. With more than " +
            "30 years of diligent practice and learning under the supervision of Grandmaster Gin Soon Chu and his son, Vincent Chu, Tony Zhu " +
            "has mastered the Yang style Tai Chi Chuan.",
        image: tonyZhuImage,
    }
];

export const lineage = [
    {
        key: "yang-lu-chan",
        name: "Yeung Lou Sim (Yang Luchan - Yang Fukui)",
        lifespan: "1799 - 1872",
        description: "Founder of the Yang Family Style of Tai Chi Chuan. Born in Hebei Province, he trained with Master Chen Changxing in the \"Lao Jia\" style " +
            "and later developed his own form of Tai Chi Chuan. His modifications made Tai Chi accessible to a wider audience. He trained his sons, " +
            "including Yeung Ban Hou and Yeung Kin Hou, who continued his legacy.",
        image: yeungLouSimImage,
    },
    {
        key: "yang-kin-hou",
        name: "Yeung Kin Hou (Yang-Chian)",
        lifespan: "1839 - 1917",
        description: "Third son of Yeung Lou Sim. He refined the Yang Style into \"Jhong Jia\" (Medium Frame), which later evolved into the \"Da Jia\" (Big Frame) " +
            "style by his son Yeung Ching Po. His work was instrumental in creating the modern Yang Style Tai Chi Chuan.",
        image: yeungKinHouImage,
    },
    {
        key: "yang-ban-hou",
        name: "Yang-Yu (Yeung Ban Hou)",
        lifespan: "1837 - 1892",
        description: "Second son of Yeung Lou Sim. Creator of the \"Xiao Jia\" (Small Frame) style of Tai Chi. Though a skilled martial artist, he preferred not to " +
            "teach and had few students, including his nephew Yeung Shaohou.",
        image: yeungBanHouImage,
    },
    {
        key: "yang-shao-hou",
        name: "Yeung Siu Hou (Yang Shaohou)",
        lifespan: "1862 - 1930",
        description: "Eldest son of Yeung Kin Hou, known for his high stance, powerful blows, and quick, ferocious attacks. Despite his mastery, his style of Tai Chi " +
            "remained less popular than that of his younger brother, Yeung Ching Po.",
        image: yeungSiuHouImage,
    },
    {
        key: "yang-cheng-fu",
        name: "Yeung Ching Po (Yang Chengfu)",
        lifespan: "1883 - 1936",
        description: "Third son of Yeung Kin Hou, credited with standardizing the \"Da Jia\" (Big Frame) style of Tai Chi Chuan. His emphasis on natural postures, " +
            "slow and even movements made Tai Chi Chuan widely popular and established it as the most recognized form today.",
        image: yeungChingPoImage,
    },
    {
        key: "yeung-sau-chung",
        name: "Yeung Sau Chung",
        lifespan: "1910 - 1985",
        description: "Eldest son of Yeung Ching Po. Known for propagating the family art of Tai Chi Chuan globally. He authored books and taught disciples who " +
            "continued his legacy in Hong Kong, the United States, and the United Kingdom.",
        image: yeungSauChungImage,
    },
    {
        key: "yeung-daughters",
        name: "Yeung Tai Yee, Yeung Ma Lee, Yeung Yee Li",
        lifespan: "1950s - Present",
        description: "Daughters of Yeung Sau Chung, they continue their father's legacy by teaching Tai Chi Chuan in Hong Kong. They are renowned for their dedication " +
            "to preserving the Yang Family art.",
        image: yeungTaiYeeImage,
    },
    {
        key: "ip-tai-tak",
        name: "Ip Tai Tak",
        lifespan: "1929 - 2004",
        description: "Chief disciple of Yeung Sau Chung, he began training with the Grandmaster in 1954. He propagated Tai Chi Chuan extensively and is remembered " +
            "as a key figure in continuing the Yang Family teachings.",
        image: ipTaiTakImage,
    },
];

const lineageByKey = Object.fromEntries(lineage.map(person => [person.key, person]));

// The line of teachers from the founder of the Yang style to Vincent Chu, oldest first
export const teacherLine = [
    { name: "Yang Lu Chan", lifespan: lineageByKey["yang-lu-chan"].lifespan, image: lineageByKey["yang-lu-chan"].image },
    { name: "Yang Kin Hou", lifespan: lineageByKey["yang-kin-hou"].lifespan, image: lineageByKey["yang-kin-hou"].image },
    { name: "Yang Cheng Fu", lifespan: lineageByKey["yang-cheng-fu"].lifespan, image: lineageByKey["yang-cheng-fu"].image },
    { name: "Yeung Sau Chung", lifespan: lineageByKey["yeung-sau-chung"].lifespan, image: lineageByKey["yeung-sau-chung"].image },
    { name: "Gin Soon Chu", image: ginSoonChu.image },
    { name: "Vincent Chu", image: vincentChu.image },
];

// The people in teacherLine before Gin Soon Chu, with their full lineage entries
export const teacherLineAncestors = ["yang-lu-chan", "yang-kin-hou", "yang-cheng-fu", "yeung-sau-chung"].map(key => lineageByKey[key]);

export const school = {
    founded: "The Gin Soon Tai Chi Club was founded in 1969 with permission from Grandmaster " +
        "Yeung Sau Chung to propagate the Yang Style Tai Chi Chuan in North America. It is the " +
        "oldest school teaching Tai Chi Chuan in the Greater Boston Area today.",
    difference: "Although there are many schools of Tai Chi Chuan available in the United States, " +
        "the Gin Soon Tai Chi Club is different from others because its founder Master Gin Soon Chu, " +
        "is a disciple who studied with and was authorized to teach by Grandmaster Yang Sau-Chung, " +
        "firstborn and heir of the legendary Yang Cheng-Fu.",
    federation: "Over the years, many students have graduated from the school and became instructors themselves. " +
        "In 1995, the Gin Soon Tai Chi Chuan Federation was established to better serve our members who " +
        "come from different countries.",
    // One line for short introductions
    summary: "Founded in 1969 with Grandmaster Yeung Sau Chung's permission, the Gin Soon Tai Chi Club is the oldest Tai Chi school in Greater Boston.",
    address: ["33 Harrison Avenue, 5th floor", "Boston, MA 02111"],
    phone: "(617) 542-4442",
    email: "chu.v@usa.com",
    images: { founded: GSCYSC, difference: GinSoonBall, federation: GinSoonSnakeCreep, contact: GinSoonPerryPunch },
};
