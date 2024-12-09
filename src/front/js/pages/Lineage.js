import React from "react";

export const Lineage = () => {
	// Lineage data
	const lineage = [
		{
			name: "Yeung Lou Sim (Yang Luchan - Yang Fukui)",
			lifespan: "1799 - 1872",
			description: `
				Founder of the Yang Family Style of Tai Chi Chuan. Born in Hebei Province, he trained with Master Chen Changxing in the "Lao Jia" style 
				and later developed his own form of Tai Chi Chuan. His modifications made Tai Chi accessible to a wider audience. He trained his sons,
				including Yeung Ban Hou and Yeung Kin Hou, who continued his legacy.
			`,
			image: "https://via.placeholder.com/300x200?text=Yeung+Lou+Sim",
		},
		{
			name: "Yeung Kin Hou (Yang-Chian)",
			lifespan: "1839 - 1917",
			description: `
				Third son of Yeung Lou Sim. He refined the Yang Style into "Jhong Jia" (Medium Frame), which later evolved into the "Da Jia" (Big Frame)
				style by his son Yeung Ching Po. His work was instrumental in creating the modern Yang Style Tai Chi Chuan.
			`,
			image: "https://via.placeholder.com/300x200?text=Yeung+Kin+Hou",
		},
		{
			name: "Yang-Yu (Yeung Ban Hou)",
			lifespan: "1837 - 1892",
			description: `
				Second son of Yeung Lou Sim. Creator of the "Xiao Jia" (Small Frame) style of Tai Chi. Though a skilled martial artist, he preferred not to 
				teach and had few students, including his nephew Yeung Shaohou.
			`,
			image: "https://via.placeholder.com/300x200?text=Yeung+Ban+Hou",
		},
		{
			name: "Yeung Siu Hou (Yang Shaohou)",
			lifespan: "1862 - 1930",
			description: `
				Eldest son of Yeung Kin Hou, known for his high stance, powerful blows, and quick, ferocious attacks. Despite his mastery, his style of Tai Chi 
				remained less popular than that of his younger brother, Yeung Ching Po.
			`,
			image: "https://via.placeholder.com/300x200?text=Yeung+Siu+Hou",
		},
		{
			name: "Yeung Ching Po (Yang Chengfu)",
			lifespan: "1883 - 1936",
			description: `
				Third son of Yeung Kin Hou, credited with standardizing the "Da Jia" (Big Frame) style of Tai Chi Chuan. His emphasis on natural postures, 
				slow and even movements made Tai Chi Chuan widely popular and established it as the most recognized form today.
			`,
			image: "https://via.placeholder.com/300x200?text=Yeung+Ching+Po",
		},
		{
			name: "Yeung Sau Chung",
			lifespan: "1910 - 1985",
			description: `
				Eldest son of Yeung Ching Po. Known for propagating the family art of Tai Chi Chuan globally. He authored books and taught disciples who 
				continued his legacy in Hong Kong, the United States, and the United Kingdom.
			`,
			image: "https://via.placeholder.com/300x200?text=Yeung+Sau+Chung",
		},
		{
			name: "Yeung Tai Yee, Yeung Ma Lee, Yeung Yee Li",
			lifespan: "1950s - Present",
			description: `
				Daughters of Yeung Sau Chung, they continue their father's legacy by teaching Tai Chi Chuan in Hong Kong. They are renowned for their dedication 
				to preserving the Yang Family art.
			`,
			image: "https://via.placeholder.com/300x200?text=Yeung+Tai+Yee+%26+Sisters",
		},
		{
			name: "Ip Tai Tak",
			lifespan: "1929 - 2004",
			description: `
				Chief disciple of Yeung Sau Chung, he began training with the Grandmaster in 1954. He propagated Tai Chi Chuan extensively and is remembered 
				as a key figure in continuing the Yang Family teachings.
			`,
			image: "https://via.placeholder.com/300x200?text=Ip+Tai+Tak",
		},
	];

	return (
		<div className="container my-5">
			<h1 className="text-center mb-4">Yang Style Tai Chi Lineage</h1>
			<div className="row">
				{lineage.map((person, index) => (
					<div key={index} className="col-md-6 mb-4">
						<div className="card shadow-sm h-100">
							<img
								src={person.image}
								className="card-img-top"
								alt={person.name}
							/>
							<div className="card-body">
								<h4 className="card-title">{person.name}</h4>
								<p className="card-subtitle text-muted">{person.lifespan}</p>
								<p className="card-text mt-3" style={{ textAlign: "justify" }}>
									{person.description}
								</p>
							</div>
						</div>
					</div>
				))}
			</div>
		</div>
	);
};
